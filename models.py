# -*- coding: utf-8 -*-
"""Application models."""

import csv
import json
import random
import re
import string
import uuid
import yaml
import os
from collections import namedtuple
from datetime import datetime
from hashlib import md5
from io import StringIO
from itertools import zip_longest
from urllib.parse import urlencode

from flask_login import UserMixin, current_user
from peewee import BooleanField as BooleanField_
from peewee import (CharField, DateTimeField, DeferredRelation, Field, FixedCharField,
                    ForeignKeyField, IntegerField, Model, OperationalError, PostgresqlDatabase,
                    ProgrammingError, SmallIntegerField, TextField, fn)
from peewee_validates import ModelValidator
from playhouse.shortcuts import model_to_dict
from pycountry import countries
from pykwalify.core import Core

from application import app, db
from config import DEFAULT_COUNTRY, ENV

EMAIL_REGEX = re.compile(r"^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$")

AFFILIATION_TYPES = (
    "student",
    "education",
    "staff",
    "employment",
)

try:
    from enum import IntFlag
except ImportError:
    from enum import IntEnum as IntFlag


class ModelException(Exception):
    """Applicaton model exception."""

    pass


def validate_orcid_id(value):
    """Validate ORCID iD (both format and the check-sum)."""
    if not value:
        return

    if not re.match(r"^\d{4}-?\d{4}-?\d{4}-?\d{4}$", value):
        raise ValueError(
            "Invalid ORCID iD. It should be in the form of 'xxxx-xxxx-xxxx-xxxx' where x is a digit."
        )
    check = 0
    for n in value:
        if n == '-':
            continue
        check = (2 * check + int(10 if n == 'X' else n)) % 11
    if check != 1:
        raise ValueError("Invalid ORCID iD checksum. Make sure you have entered correct ORCID iD.")


class PartialDate(namedtuple("PartialDate", ["year", "month", "day"])):
    """Partial date (without month day or both moth and month day."""

    def as_orcid_dict(self):
        """Return ORCID dictionry representation of the partial date."""
        if self.year is None and self.month is None and self.day is None:
            return None
        return dict(((f, None if v is None else {
            "value": ("%04d" if f == "year" else "%02d") % v
        }) for (f, v) in zip(self._fields, self)))

    @classmethod
    def create(cls, value):
        """Create a partial date form ORCID dictionary representation or string.

        >>> PartialDate.create({"year": {"value": "2003"}}).as_orcid_dict()
        {'year': {'value': '2003'}, 'month': None, 'day': None}

        >>> PartialDate.create({"year": {"value": "2003"}}).year
        2003

        >>> PartialDate.create("2003").year
        2003

        >>> PartialDate.create("2003-03")
        2003-03

        >>> PartialDate.create("2003-07-14")
        2003-07-13
        """
        if value is None or value == {}:
            return None
        if isinstance(value, str):
            try:
                return cls(*[int(v) for v in value.split('-')])
            except Exception as ex:
                raise ModelException(f"Wrong partial date value '{value}': {ex}")

        return cls(**{k: int(v.get("value")) if v else None for k, v in value.items()})

    def as_datetime(self):
        """Get 'datetime' data representation."""
        return datetime(self.year, self.month, self.day)

    def __str__(self):
        """Get string representation."""
        if self.year is None:
            return ''
        else:
            res = "%04d" % int(self.year)
            if self.month:
                res += "-%02d" % int(self.month)
            return res + "-%02d" % int(self.day) if self.day else res


PartialDate.__new__.__defaults__ = (None, ) * len(PartialDate._fields)


class OrcidIdField(FixedCharField):
    """ORCID iD value DB field."""

    def __init__(self, *args, **kwargs):
        """Initialize ORCID iD data field."""
        if "verbose_name" not in kwargs:
            kwargs["verbose_name"] = "ORCID iD"
        super().__init__(*args, max_length=19, **kwargs)

    # TODO: figure out where to place the value validation...
    # def coerce(self, value):
    #     validate_orcid_id(value)
    #     return super().coerce(value)


class BooleanField(BooleanField_):
    """BooleanField extension to support inversion in queries."""

    def NOT(self):  # noqa: N802
        """Negate logical value in SQL."""
        return self.__invert__()


class PartialDateField(Field):
    """Partial date custom DB data field mapped to varchar(10)."""

    db_field = "varchar(10)"

    def db_value(self, value):
        """Convert into partial ISO date textual representation: YYYY-**-**, YYYY-MM-**, or YYYY-MM-DD."""
        if value is None or not value.year:
            return None
        else:
            res = "%04d" % int(value.year)
            if value.month:
                res += "-%02d" % int(value.month)
            else:
                return res + "-**-**"
            return res + "-%02d" % int(value.day) if value.day else res + "-**"

    def python_value(self, value):
        """Parse partial ISO date textual representation."""
        if value is None:
            return None

        parts = [int(p) for p in value.split("-") if "*" not in p]
        return PartialDate(**dict(zip_longest((
            "year",
            "month",
            "day",
        ), parts)))


class Role(IntFlag):
    """
    Enum used to represent user role.

    The model provide multi role support representing role sets as bitmaps.
    """

    NONE = 0  # NONE
    SUPERUSER = 1  # SuperUser
    ADMIN = 2  # Admin
    RESEARCHER = 4  # Researcher
    TECHNICAL = 8  # Technical contact
    ANY = 255  # ANY

    def __eq__(self, other):
        if isinstance(other, Role):
            return self.value == other.value
        return (self.name == other or self.name == getattr(other, 'name', None))

    def __hash__(self):
        return hash(self.name)


class Affiliation(IntFlag):
    """
    Enum used to represent user affiliation (type) to the organisation.

    The model provide multiple affiliations support representing role sets as bitmaps.
    """

    NONE = 0  # NONE
    EDU = 1  # Education
    EMP = 2  # Employment

    def __eq__(self, other):
        if isinstance(other, Affiliation):
            return self.value == other.value
        return (self.name == other or self.name == getattr(other, 'name', None))

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return ", ".join({
            self.EDU: "Education",
            self.EMP: "Employment"
        }[a] for a in Affiliation if a & self)


class BaseModel(Model):
    """Encapsulate commont bits and pieces of the model classes."""

    def field_is_updated(self, field_name):
        """Test if field is 'dirty'."""
        return any(field_name == f.name for f in self.dirty_fields)

    @classmethod
    def model_class_name(cls):
        """Get the class name of the model."""
        return cls._meta.name

    def to_dict(self):
        """Get dictionary representation of the model."""
        return model_to_dict(self)

    class Meta:  # noqa: D101,D106
        database = db
        only_save_dirty = True


class ModelDeferredRelation(DeferredRelation):
    """Fixed DefferedRelation to allow inheritance and mixins."""

    def set_model(self, rel_model):
        """Include model in the generated "related_name" to make it unique."""
        for model, field, name in self.fields:
            if isinstance(field, ForeignKeyField) and not field._related_name:
                field._related_name = "%s_%s_set" % (model.model_class_name(), name)

        super().set_model(rel_model)


DeferredUser = ModelDeferredRelation()


class AuditMixin(Model):
    """Mixing for getting data necessary for data change audit trail maintenace."""

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(null=True)

    # created_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)
    # updated_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)

    def save(self, *args, **kwargs):  # noqa: D102
        if self.is_dirty():
            self.updated_at = datetime.now()
            if current_user and hasattr(current_user, "id"):
                if hasattr(self, "created_by") and self.created_by and hasattr(self, "updated_by"):
                    self.updated_by_id = current_user.id
                elif hasattr(self, "created_by"):
                    self.created_by_id = current_user.id
        return super().save(*args, **kwargs)


class Organisation(BaseModel, AuditMixin):
    """Research oranisation."""

    country_choices = [(c.alpha_2, c.name) for c in countries]
    country_choices.sort(key=lambda e: e[1])
    country_choices.insert(0, ("", "Country"))

    name = CharField(max_length=100, unique=True, null=True)
    tuakiri_name = CharField(max_length=80, unique=True, null=True)
    if ENV != "prod":
        orcid_client_id = CharField(max_length=80, null=True)
        orcid_secret = CharField(max_length=80, null=True)
    else:
        orcid_client_id = CharField(max_length=80, unique=True, null=True)
        orcid_secret = CharField(max_length=80, unique=True, null=True)
    confirmed = BooleanField(default=False)
    city = CharField(null=True)
    state = CharField(null=True, verbose_name="State/Region", max_length=100)
    country = CharField(null=True, choices=country_choices, default=DEFAULT_COUNTRY)
    disambiguated_id = CharField(null=True)
    disambiguation_source = CharField(null=True)
    is_email_sent = BooleanField(default=False)
    tech_contact = ForeignKeyField(
        DeferredUser,
        related_name="tech_contact_for",
        on_delete="SET NULL",
        null=True,
        help_text="Organisation technical contact")
    created_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)
    updated_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)

    api_credentials_requested_at = DateTimeField(
        null=True,
        help_text="The time stamp when the user clicked on the button to register client API.")
    api_credentials_entered_at = DateTimeField(
        null=True, help_text="The time stamp when the user entered API Client ID and secret.")

    @property
    def invitation_sent_to(self):
        """Get the most recent invitation recepient."""
        try:
            return (self.orginvitation_set.select(
                OrgInvitation.invitee).where(OrgInvitation.invitee_id == self.tech_contact_id)
                    .order_by(OrgInvitation.created_at.desc()).first().invitee)
        except Exception:
            return None

    @property
    def invitation_sent_at(self):
        """Get the timestamp of the most recent invitation sent to the technical contact."""
        try:
            return (self.orginvitation_set.select(
                fn.MAX(OrgInvitation.created_at).alias("last_sent_at")).where(
                    OrgInvitation.invitee_id == self.tech_contact_id).first().last_sent_at)
        except Exception:
            return None

    @property
    def invitation_confirmed_at(self):
        """Get the timestamp when the invitation link was opened."""
        try:
            return (self.orginvitation_set.select(
                fn.MAX(OrgInvitation.created_at).alias("last_confirmed_at")).where(
                    OrgInvitation.invitee_id == self.tech_contact_id).where(
                        OrgInvitation.confirmed_at.is_null(False)).first().last_confirmed_at)
        except Exception:
            return None

    @property
    def users(self):
        """Get organisation's user query."""
        return User.select().join(
            UserOrg, on=(UserOrg.user_id == User.id)).where(UserOrg.org == self)

    @property
    def admins(self):
        """Get organisation's adminstrator query."""
        return self.users.where(UserOrg.is_admin)

    def __repr__(self):
        return self.name or self.tuakiri_name

    def save(self, *args, **kwargs):
        """Handle data consitency validation and saving."""
        if self.is_dirty():

            if self.name is None:
                self.name = self.tuakiri_name

            if self.field_is_updated("tech_contact"):
                if not self.tech_contact.has_role(Role.TECHNICAL):
                    self.tech_contact.roles |= Role.TECHNICAL
                    self.tech_contact.save()
                    app.logger.info(f"Added TECHNICAL role to user {self.tech_contact}")

        super().save(*args, **kwargs)


class OrgInfo(BaseModel):
    """Preloaded organisation data."""

    name = CharField(max_length=100, unique=True, verbose_name="Organisation")
    tuakiri_name = CharField(max_length=100, unique=True, null=True, verbose_name="TUAKIRI Name")
    title = CharField(null=True, verbose_name="Contact person tile")
    first_name = CharField(null=True, verbose_name="Contact person's first name")
    last_name = CharField(null=True, verbose_name="Contact person's last name")
    role = CharField(null=True, verbose_name="Contact person's role")
    email = CharField(null=True, verbose_name="Contact person's email")
    phone = CharField(null=True, verbose_name="Contact person's phone")
    is_public = BooleanField(
        null=True, default=False, verbose_name="Permission to post contact information to WEB")
    country = CharField(null=True, verbose_name="Country Code", default=DEFAULT_COUNTRY)
    city = CharField(null=True, verbose_name="City of home campus")
    disambiguated_id = CharField(
        null=True, verbose_name="common:disambiguated-organization-identifier")
    disambiguation_source = CharField(null=True, verbose_name="common:disambiguation-source")

    def __repr__(self):
        return self.name or self.disambiguated_id or super().__repr__()

    class Meta:  # noqa: D101,D106
        db_table = "org_info"
        table_alias = "oi"

    @classmethod
    def load_from_csv(cls, source):
        """Load data from CSV file or a string."""
        if isinstance(source, str):
            if '\n' in source:
                source = StringIO(source)
            else:
                source = open(source)
        reader = csv.reader(source)
        header = next(reader)

        assert len(header) >= 3, \
            "Wrong number of fields. Expected at least 3 fields " \
            "(name, disambiguated organisation ID, and disambiguation source). " \
            "Read header: %s" % header
        header_rexs = [
            re.compile(ex, re.I)
            for ex in ("organisation|name", "title", r"first\s*(name)?", r"last\s*(name)?", "role",
                       "email", "phone", "public|permission to post to web", r"country\s*(code)?",
                       "city", "(common:)?disambiguated.*identifier",
                       "(common:)?disambiguation.*source", r"tuakiri\s*(name)?")
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        def val(row, i, default=None):
            if idxs[i] is None:
                return default
            else:
                v = row[idxs[i]].strip()
                return None if v == '' else v

        for row in reader:
            name = val(row, 0)
            oi, _ = cls.get_or_create(name=name)

            oi.title = val(row, 1)
            oi.first_name = val(row, 2)
            oi.last_name = val(row, 3)
            oi.role = val(row, 4)
            oi.email = val(row, 5)
            oi.phone = val(row, 6)
            oi.is_public = val(row, 7) and val(row, 7).upper() == "YES"
            oi.country = val(row, 8) or DEFAULT_COUNTRY
            oi.city = val(row, 9)
            oi.disambiguated_id = val(row, 10)
            oi.disambiguation_source = val(row, 11)
            oi.tuakiri_name = val(row, 12)

            oi.save()

        return reader.line_num - 1


class User(BaseModel, UserMixin, AuditMixin):
    """
    ORCiD Hub user.

    It's a gneric user including researchers, organisation administrators, hub administrators, etc.
    """

    name = CharField(max_length=64, null=True)
    first_name = CharField(null=True, verbose_name="Firs Name")
    last_name = CharField(null=True, verbose_name="Last Name")
    email = CharField(max_length=120, unique=True, null=True)
    eppn = CharField(max_length=120, unique=True, null=True)
    # ORCiD:
    orcid = OrcidIdField(null=True)
    confirmed = BooleanField(default=False)
    # Role bit-map:
    roles = SmallIntegerField(default=0)

    is_locked = BooleanField(default=False)

    # TODO: many-to-many
    # NB! depricated!
    # TODO: we still need to rememeber the rognanistiaon that last authenticated the user
    organisation = ForeignKeyField(
        Organisation, related_name="members", on_delete="CASCADE", null=True)
    created_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)
    updated_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)

    def __repr__(self):
        if self.name and (self.eppn or self.email):
            return "%s (%s)" % (self.name, self.email or self.eppn)
        return self.name or self.email or self.orcid or super().__repr__()

    @property
    def organisations(self):
        """Get all linked to the user organisation query."""
        return Organisation.select().join(
            UserOrg, on=(UserOrg.org_id == Organisation.id)).where(UserOrg.user_id == self.id)

    @property
    def admin_for(self):
        """Get organisations the user is admin for (query)."""
        return self.organisations.where(UserOrg.is_admin)

    @property
    def is_active(self):
        """Get 'is_active' based on confirmed for Flask-Login.

        TODO: confirmed - user that email is cunfimed either by IdP or by confirmation email
        ins't the same as "is active".
        """
        return self.confirmed

    def has_role(self, role):
        """Return `True` if the user identifies with the specified role.

        :param role: A role name, `Role` instance, or integer value.
        """
        if isinstance(role, Role):
            return bool(role & Role(self.roles))
        elif isinstance(role, str):
            try:
                return bool(Role[role.upper()] & Role(self.roles))
            except Exception:
                False
        elif type(role) is int:
            return bool(role & self.roles)
        else:
            return False

    @property
    def is_superuser(self):
        """Test if the user is a HUB admin."""
        return bool(self.roles & Role.SUPERUSER)

    @is_superuser.setter
    def is_superuser(self, value):  # noqa: D401
        """Sets user as a HUB admin."""
        if value:
            self.roles |= Role.SUPERUSER
        else:
            self.roles ^= Role.SUPERUSER

    @property
    def is_admin(self):
        """Test if the user belongs to the organisation admin."""
        return bool(self.roles & Role.ADMIN)

    def avatar(self, size=40, default="identicon"):
        """Return Gravatar service user avatar URL."""
        # TODO: default gravatar image
        # default = "https://www.example.com/default.jpg"
        gravatar_url = "https://www.gravatar.com/avatar/" + md5(
            self.email.lower().encode()).hexdigest() + "?"
        gravatar_url += urlencode({'d': default, 's': str(size)})
        return gravatar_url

    @property
    def gravatar_profile_url(self):
        """Return Gravatar service user profile URL."""
        return "https://www.gravatar.com/" + md5(self.email.lower().encode()).hexdigest()

    @property
    def affiliations(self):
        """Return affiliations with the current organisation."""
        try:
            user_org = UserOrg.get(user=self, org=self.organisation)
            return Affiliation(user_org.affiliations)
        except UserOrg.DoesNotExist:
            return Affiliation.NONE

    def is_tech_contact_of(self, org=None):
        """Indicats if the user is the technical contact of the organisation."""
        if org is None:
            org = self.organisation
        return org and org.tech_contact and org.tech_contact_id == self.id

    @staticmethod
    def load_from_csv(source):
        """Load data from CSV file or a string."""
        if isinstance(source, str):
            if '\n' in source:
                source = StringIO(source)
            else:
                source = open(source)
        reader = csv.reader(source)
        header = next(reader)

        assert len(header) >= 4, \
            "Wrong number of fields. Expected at least 4 fields " \
            "(first Name, Last Name, affiliation and email). " \
            "Read header: %s" % header
        header_rexs = [
            re.compile(ex, re.I)
            for ex in (r"first\s*(name)?", r"last\s*(name)?", "email\s*(address)?",
                       "affiliation|student/staff")
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        def val(row, i):
            if idxs[i] is None:
                return None
            else:
                v = row[idxs[i]].strip()
                return None if v == '' else v

        org = Organisation.get(name=current_user.organisation.name)
        users = {}
        for row in reader:
            email = val(row, 2).encode("latin-1").decode("utf-8").lower()
            user, _ = User.get_or_create(email=email)

            user.first_name = val(row, 0).encode("latin-1").decode("utf-8")
            user.last_name = val(row, 1).encode("latin-1").decode("utf-8")
            user.roles = Role.RESEARCHER
            user.email = email
            user.organisation = org
            user.save()
            users[user.email] = user
            user_org, user_org_created = UserOrg.get_or_create(user=user, org=org)

            if val(row, 3):
                unscoped_affiliation = set(a.strip()
                                           for a in val(row, 3).encode("latin-1")
                                           .decode("utf-8").lower().replace(',', ';').split(';'))

                edu_person_affiliation = Affiliation.NONE
                if unscoped_affiliation & {"faculty", "staff"}:
                    edu_person_affiliation |= Affiliation.EMP
                if unscoped_affiliation & {"student"}:
                    edu_person_affiliation |= Affiliation.EDU
                user_org.affiliations = edu_person_affiliation
            user_org.save()

        return users

    @property
    def uuid(self):
        """Generate UUID for the user basee on the the primary email."""
        return uuid.uuid5(uuid.NAMESPACE_URL, "mailto:" + (self.email or self.eppn))


DeferredUser.set_model(User)


class OrgInvitation(BaseModel, AuditMixin):
    """Organisation invitation to on-board the Hub."""

    invitee = ForeignKeyField(
        User, on_delete="CASCADE", null=True, related_name="received_org_invitations")
    inviter = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="sent_org_invitations")
    org = ForeignKeyField(Organisation, on_delete="SET NULL", verbose_name="Organisation")
    email = TextField(help_text="The email address the invitation was sent to.")
    token = TextField(unique=True)
    confirmed_at = DateTimeField(null=True)

    @property
    def sent_at(self):
        """Get the time the invitation was sent."""
        return self.created_at

    class Meta:  # noqa: D101,D106
        db_table = "org_invitation"


class UserOrg(BaseModel, AuditMixin):
    """Linking object for many-to-many relationship."""

    user = ForeignKeyField(User, on_delete="CASCADE", index=True)
    org = ForeignKeyField(
        Organisation, on_delete="CASCADE", index=True, verbose_name="Organisation")

    is_admin = BooleanField(
        default=False, help_text="User is an administrator for the organisation")

    # Affiliation bit-map:
    affiliations = SmallIntegerField(default=0, null=True, verbose_name="EDU Person Affiliations")
    created_by = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="created_user_orgs")
    updated_by = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="updated_user_orgs")

    # TODO: the access token should be either here or in a separate list
    # access_token = CharField(max_length=120, unique=True, null=True)

    def save(self, *args, **kwargs):
        """Enforce foriegn key contraints and consolidate user roles with the linked organisations.

        Enforce foriegn key contraints and consolidate user roles with the linked organisations
        before saving data.
        """
        if self.is_dirty():
            if self.field_is_updated("org"):
                self.org  # just enforce re-querying
            user = self.user
            if self.is_admin != user.is_admin:
                if self.is_admin or UserOrg.select().where((UserOrg.user_id == self.user_id) & (
                        UserOrg.org_id != self.org_id) & UserOrg.is_admin).exists():  # noqa: E125
                    user.roles |= Role.ADMIN
                    app.logger.info(f"Added ADMIN role to user {user}")
                else:
                    user.roles &= ~Role.ADMIN
                    app.logger.info(f"Revoked ADMIN role from user {user}")
                user.save()

        return super().save(*args, **kwargs)

    class Meta:  # noqa: D101,D106
        db_table = "user_org"
        table_alias = "uo"
        indexes = ((("user", "org"), True), )


class OrcidToken(BaseModel, AuditMixin):
    """For Keeping Orcid token in the table."""

    user = ForeignKeyField(User)
    org = ForeignKeyField(Organisation, index=True, verbose_name="Organisation")
    scope = TextField(null=True)
    access_token = CharField(max_length=36, unique=True, null=True)
    issue_time = DateTimeField(default=datetime.now)
    refresh_token = CharField(max_length=36, unique=True, null=True)
    expires_in = SmallIntegerField(default=0)
    created_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)
    updated_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)


class UserOrgAffiliation(BaseModel, AuditMixin):
    """For Keeping the information about the affiliation."""

    user = ForeignKeyField(User)
    organisation = ForeignKeyField(Organisation, index=True, verbose_name="Organisation")
    name = TextField(null=True, verbose_name="Institution/employer")
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    department_name = TextField(null=True)
    department_city = TextField(null=True)
    role_title = TextField(null=True)
    put_code = IntegerField(null=True)
    path = TextField(null=True)
    created_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)
    updated_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)

    class Meta:  # noqa: D101,D106
        db_table = "user_organisation_affiliation"
        table_alias = "oua"


class OrcidApiCall(BaseModel):
    """ORCID API call audit entry."""

    called_at = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, null=True)
    method = TextField()
    url = TextField()
    query_params = TextField(null=True)
    body = TextField(null=True)
    put_code = IntegerField(null=True)
    response = TextField(null=True)
    response_time_ms = IntegerField(null=True)

    class Meta:  # noqa: D101,D106
        db_table = "orcid_api_call"


class OrcidAuthorizeCall(BaseModel):
    """ORCID Authorize call audit entry."""

    called_at = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, null=True)
    method = TextField(null=True)
    url = TextField(null=True)
    token = TextField(null=True)
    state = TextField(null=True)
    response_time_ms = IntegerField(null=True)

    class Meta:  # noqa: D101,D106
        db_table = "orcid_authorize_call"


class Task(BaseModel, AuditMixin):
    """Batch processing task created form CSV/TSV file."""

    __record_count = None
    __record_funding_count = None
    org = ForeignKeyField(
        Organisation, index=True, verbose_name="Organisation", on_delete="SET NULL")
    completed_at = DateTimeField(null=True)
    filename = TextField(null=True)
    created_by = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="created_tasks")
    updated_by = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="updated_tasks")
    task_type = SmallIntegerField(default=0, null=True)

    def __repr__(self):
        return self.filename or f"Task #{self.id}"

    @property
    def record_count(self):
        """Get count of the loaded recoreds."""
        if self.__record_count is None:
            self.__record_count = self.affiliationrecord_set.count()
        return self.__record_count

    @property
    def record_funding_count(self):
        """Get count of the loaded funding records."""
        if self.__record_funding_count is None:
            self.__record_funding_count = self.funding_records.count()
        return self.__record_funding_count

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load data from CSV/TSV file or a string."""
        if isinstance(source, str):
            if '\n' in source:
                source = StringIO(source)
            else:
                source = open(source)
                if filename is None:
                    filename = source
        reader = csv.reader(source)
        header = next(reader)
        if filename is None:
            if hasattr(source, "name"):
                filename = source.name
            else:
                filename = datetime.now().isoformat(timespec="seconds")

        if len(header) == 1 and '\t' in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter='\t')
            header = next(reader)
        if len(header) < 2:
            raise ModelException("Expected CSV or TSV format file.")

        assert len(header) >= 7, \
            "Wrong number of fields. Expected at least 7 fields " \
            "(first name, last name, email address, organisation, " \
            "campus/department, city, course or job title, start date, end date, student/staff). " \
            f"Read header: {header}"
        header_rexs = [
            re.compile(ex, re.I)
            for ex in (r"first\s*(name)?", r"last\s*(name)?", "email", "organisation|^name",
                       "campus|department", "city", "state|region", "course|title|role",
                       r"start\s*(date)?", r"end\s*(date)?",
                       r"affiliation(s)?\s*(type)?|student|staff", "country", r"disambiguat.*id",
                       r"disambiguat.*source", r"put|code", "orcid", "external.*|.*identifier")
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        if all(idx is None for idx in idxs):
            raise ModelException(f"Failed to map fields based on the header of the file: {header}")

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, i, default=None):
            if idxs[i] is None or idxs[i] >= len(row):
                return default
            else:
                v = row[idxs[i]].strip()
                return default if v == '' else v

        with db.atomic():
            try:
                task = cls.create(org=org, filename=filename)
                for row_no, row in enumerate(reader):
                    if len(row) == 0:
                        continue

                    email = val(row, 2, "").lower()
                    orcid = val(row, 15)

                    if not (email or orcid):
                        raise ModelException(
                            f"Missing user identifier (email address or ORCID iD) in the row #{row_no+2}: {row}"
                        )

                    if orcid:
                        try:
                            validate_orcid_id(orcid)
                        except Exception as ex:
                            pass

                    if not email or not EMAIL_REGEX.match(email):
                        raise ValueError(
                            f"Invalid email address '{email}'  in the row #{row_no+2}: {row}")

                    affiliation_type = val(row, 10, "").lower()
                    if not affiliation_type or affiliation_type not in AFFILIATION_TYPES:
                        raise ValueError(
                            f"Invalid affiliation type '{affiliation_type}' in the row #{row_no+2}: {row}. "
                            f"Expected values: {', '.join(at for at in AFFILIATION_TYPES)}.")

                    af = AffiliationRecord(
                        task=task,
                        first_name=val(row, 0),
                        last_name=val(row, 1),
                        email=email,
                        organisation=val(row, 3),
                        department=val(row, 4),
                        city=val(row, 5),
                        region=val(row, 6),
                        role=val(row, 7),
                        start_date=PartialDate.create(val(row, 8)),
                        end_date=PartialDate.create(val(row, 9)),
                        affiliation_type=affiliation_type,
                        country=val(row, 11),
                        disambiguated_id=val(row, 12),
                        disambiguated_source=val(row, 13),
                        put_code=val(row, 14),
                        orcid=orcid,
                        external_id=val(row, 16))
                    validator = ModelValidator(af)
                    if not validator.validate():
                        raise ModelException(f"Invalid record: {validator.errors}")
                    af.save()
            except Exception as ex:
                db.rollback()
                app.logger.exception("Failed to laod affiliation file.")
                raise

        return task

    class Meta:  # noqa: D101,D106
        table_alias = "t"


class UserInvitation(BaseModel, AuditMixin):
    """Organisation invitation to on-board the Hub."""

    invitee = ForeignKeyField(
        User, on_delete="CASCADE", null=True, related_name="received_user_invitations")
    inviter = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="sent_user_invitations")
    org = ForeignKeyField(
        Organisation, on_delete="CASCADE", null=True, verbose_name="Organisation")
    task = ForeignKeyField(Task, on_delete="CASCADE", null=True, index=True, verbose_name="Task")

    email = CharField(
        index=True, max_length=80, help_text="The email address the invitation was sent to.")
    first_name = TextField(null=True, verbose_name="First Name")
    last_name = TextField(null=True, verbose_name="Last Name")
    orcid = OrcidIdField(null=True)
    department = TextField(verbose_name="Campus/Department", null=True)
    organisation = TextField(verbose_name="Organisation Name", null=True)
    city = TextField(verbose_name="City", null=True)
    state = TextField(verbose_name="State", null=True)
    country = CharField(verbose_name="Country", max_length=2, null=True)
    course_or_role = TextField(verbose_name="Course or Job title", null=True)
    start_date = PartialDateField(verbose_name="Start date", null=True)
    end_date = PartialDateField(verbose_name="End date (leave blank if current)", null=True)
    affiliations = SmallIntegerField(verbose_name="User affiliations", null=True)
    disambiguated_id = TextField(verbose_name="Disambiguation ORG Id", null=True)
    disambiguation_source = TextField(verbose_name="Disambiguation ORG Source", null=True)
    token = TextField(unique=True)
    confirmed_at = DateTimeField(null=True)

    @property
    def sent_at(self):
        """Get the time the invitation was sent."""
        return self.created_at

    class Meta:  # noqa: D101,D106
        db_table = "user_invitation"


class AffiliationRecord(BaseModel):
    """Affiliation record loaded from CSV file for batch processing."""

    task = ForeignKeyField(Task)
    put_code = IntegerField(null=True)
    external_id = CharField(
        max_length=100,
        null=True,
        verbose_name="External ID",
        help_text="Record identifier used in the data source system.")
    first_name = CharField(max_length=120, null=True)
    last_name = CharField(max_length=120, null=True)
    email = CharField(max_length=80, null=True)
    orcid = OrcidIdField(null=True)
    organisation = CharField(null=True, index=True, max_length=200)
    affiliation_type = CharField(
        max_length=20, null=True, choices=[(v, v) for v in AFFILIATION_TYPES])
    role = CharField(null=True, verbose_name="Role/Course", max_length=100)
    department = CharField(null=True, max_length=200)
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    city = CharField(null=True, max_length=200)
    state = CharField(null=True, verbose_name="State/Region", max_length=100)
    country = CharField(null=True, verbose_name="Country", max_length=3)
    disambiguated_id = CharField(
        null=True, max_length=20, verbose_name="Disambiguated Organization Identifier")
    disambiguated_source = CharField(
        null=True, max_length=100, verbose_name="Disambiguation Source")

    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True)
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    def add_status_line(self, line):
        """Add a text line to the status for logging processing progress."""
        ts = datetime.now().isoformat(timespec="seconds")
        self.status = (self.status + "\n" if self.status else '') + ts + ": " + line

    class Meta:  # noqa: D101,D106
        db_table = "affiliation_record"
        table_alias = "ar"


class TaskType(IntFlag):
    """
    Enum used to represent Task type.

    The model provide multi role support representing role sets as bitmaps.
    """

    AFFILIATION = 0  # Affilation of employment/education
    FUNDING = 1  # Funding

    def __eq__(self, other):
        if isinstance(other, TaskType):
            return self.value == other.value
        return (self.name == other or self.name == getattr(other, 'name', None))

    def __hash__(self):
        return hash(self.name)


class FundingRecord(BaseModel, AuditMixin):
    """Funding record loaded from Json file for batch processing."""

    task = ForeignKeyField(Task, related_name="funding_records", on_delete="CASCADE")
    title = CharField(max_length=80)
    translated_title = CharField(null=True, max_length=80)
    type = CharField(max_length=80)
    organization_defined_type = CharField(null=True, max_length=80)
    short_description = CharField(null=True, max_length=80)
    amount = CharField(null=True, max_length=80)
    currency = CharField(null=True, max_length=3)
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    org_name = CharField(null=True, max_length=255, verbose_name="Organisation Name")
    city = CharField(null=True, max_length=255)
    region = CharField(null=True, max_length=255)
    country = CharField(null=True, max_length=255)
    disambiguated_org_identifier = CharField(null=True, max_length=255)
    disambiguation_source = CharField(null=True, max_length=255)
    visibility = CharField(null=True, max_length=100)
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True)
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load_from_json(cls, source, filename=None, org=None):
        """Load data from CSV file or a string."""
        if isinstance(source, str):
            # import data from file based on its extension; either it is yaml or json
            if os.path.splitext(filename)[1][1:] == "yaml" or "yml":
                funding_data = yaml.load(source)
            else:
                funding_data = json.loads(source)

            # Adding schema valdation for funding
            validator = Core(source_data=funding_data,      # noqa: F841
                             schema_files=["funding_schema.yaml"])

            # TODO: Uncomment the below code once "funding_schema.yaml" is fully ready
            # validator.validate(raise_exception=True)

            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                task = Task.create(org=org, filename=filename, task_type=TaskType.FUNDING)

                title = funding_data["title"]["title"]["value"] if \
                    funding_data["title"] and funding_data["title"]["title"] else None

                translated_title = funding_data["title"]["translated-title"]["value"] if \
                    funding_data["title"] and funding_data["title"]["translated-title"] else None

                type = funding_data["type"] if funding_data["type"] else None

                organization_defined_type = funding_data["organization-defined-type"]["value"] if \
                    funding_data["organization-defined-type"] else None

                short_description = funding_data["short-description"] if funding_data["short-description"] else None

                amount = funding_data["amount"]["value"] if funding_data["amount"] else None

                currency = funding_data["amount"]["currency-code"] \
                    if funding_data["amount"] and funding_data["amount"]["currency-code"] else None
                start_date = PartialDate.create(funding_data["start-date"])
                end_date = PartialDate.create(funding_data["end-date"])
                org_name = funding_data["organization"]["name"] if \
                    funding_data["organization"] and funding_data["organization"]["name"] else None

                city = funding_data["organization"]["address"]["city"] if \
                    funding_data["organization"] and funding_data["organization"]["address"] else None

                region = funding_data["organization"]["address"]["region"] if \
                    funding_data["organization"] and funding_data["organization"]["address"] else None

                country = funding_data["organization"]["address"]["country"] if \
                    funding_data["organization"] and funding_data["organization"]["address"] else None

                disambiguated_org_identifier = funding_data["organization"][
                    "disambiguated-organization"]["disambiguated-organization-identifier"] if \
                    funding_data["organization"] and \
                    funding_data["organization"]["disambiguated-organization"] else None

                disambiguation_source = funding_data["organization"][
                    "disambiguated-organization"]["disambiguation-source"] if \
                    funding_data["organization"] and \
                    funding_data["organization"]["disambiguated-organization"] else None

                visibility = funding_data["visibility"] if funding_data["visibility"] else None

                funding_record = FundingRecord.create(task=task, title=title, translated_title=translated_title,
                                                      type=type,
                                                      organization_defined_type=organization_defined_type,
                                                      short_description=short_description,
                                                      amount=amount, currency=currency, org_name=org_name, city=city,
                                                      region=region, country=country,
                                                      disambiguated_org_identifier=disambiguated_org_identifier,
                                                      disambiguation_source=disambiguation_source,
                                                      visibility=visibility, start_date=start_date, end_date=end_date)

                contributors_list = funding_data["contributors"]["contributor"]
                for contributor in contributors_list:
                    orcid_id = None
                    if contributor["contributor-orcid"] and contributor["contributor-orcid"]["path"]:
                        orcid_id = contributor["contributor-orcid"]["path"]
                    email = contributor["contributor-email"]["value"]
                    name = contributor["credit-name"]["value"]
                    role = contributor["contributor-attributes"]["contributor-role"]
                    FundingContributor.create(funding_record=funding_record, orcid=orcid_id, name=name, email=email,
                                              role=role)

                external_ids_list = funding_data["external-ids"]["external-id"]
                for external_id in external_ids_list:
                    type = external_id["external-id-type"]
                    value = external_id["external-id-value"]
                    url = external_id["external-id-url"]["value"]
                    relationship = external_id["external-id-relationship"]
                    ExternalId.create(funding_record=funding_record, type=type, value=value, url=url,
                                      relationship=relationship)

                return task
            except Exception as ex:
                db.rollback()
                app.logger.exception("Failed to laod affiliation file.")
                raise

    def add_status_line(self, line):
        """Add a text line to the status for logging processing progress."""
        ts = datetime.now().isoformat(timespec="seconds")
        self.status = (self.status + "\n" if self.status else '') + ts + ": " + line

    class Meta:  # noqa: D101,D106
        db_table = "funding_record"
        table_alias = "fr"


class FundingContributor(BaseModel):
    """Researcher or contributor - reciever of the funding."""

    funding_record = ForeignKeyField(FundingRecord, related_name="contributors")
    orcid = OrcidIdField(null=True)
    name = CharField(max_length=120, null=True)
    email = CharField(max_length=120, null=True)
    role = CharField(max_length=120, null=True)
    status = TextField(null=True, help_text="Record processing status.")
    put_code = IntegerField(null=True)
    processed_at = DateTimeField(null=True)

    def add_status_line(self, line):
        """Add a text line to the status for logging processing progress."""
        ts = datetime.now().isoformat(timespec="seconds")
        self.status = (self.status + "\n" if self.status else '') + ts + ": " + line

    class Meta:  # noqa: D101,D106
        db_table = "funding_contributor"
        table_alias = "fc"


class ExternalId(BaseModel):
    """Funding ExternalId loaded for batch processing."""

    funding_record = ForeignKeyField(FundingRecord, related_name="external_ids")
    type = CharField(max_length=80)
    value = CharField(max_length=255)
    url = CharField(max_length=200, null=True)
    relationship = CharField(max_length=80, null=True)

    class Meta:  # noqa: D101,D106
        db_table = "external_id"
        table_alias = "ei"


class Url(BaseModel, AuditMixin):
    """Shortened URLs."""

    short_id = CharField(unique=True, max_length=5)
    url = TextField()

    @classmethod
    def shorten(cls, url):
        """Create a shorten url or retrievs an exiting one."""
        try:
            u = cls.get(url=url)
        except cls.DoesNotExist:
            while True:
                short_id = ''.join(
                    random.choice(string.ascii_letters + string.digits) for _ in range(5))
                try:
                    cls.get(short_id=short_id)
                except cls.DoesNotExist:
                    u = cls.create(short_id=short_id, url=url)
                    return u
        return u


class Funding(BaseModel):
    """Uploaded research Funding record."""

    short_id = CharField(unique=True, max_length=5)
    url = TextField()


def readup_file(input_file):
    """Read up the whole content and deconde it and return the whole content."""
    raw = input_file.read()
    for encoding in "utf-8-sig", "utf-8", "utf-16":
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def create_tables():
    """Create all DB tables."""
    try:
        db.connect()
    except OperationalError:
        pass

    for model in [
            Organisation,
            User,
            UserOrg,
            OrcidToken,
            UserOrgAffiliation,
            OrgInfo,
            OrcidApiCall,
            OrcidAuthorizeCall,
            Task,
            AffiliationRecord,
            OrgInvitation,
            Url,
            UserInvitation,
            FundingRecord,
            FundingContributor,
            ExternalId,
    ]:

        try:
            model.create_table()
        except ProgrammingError as ex:
            if "already exists" in str(ex):
                app.logger.info(f"Table '{model._meta.name}' already exists")
            else:
                raise ex


def create_audit_tables():
    """Create all DB audit tables for PostgreSQL DB."""
    try:
        db.connect()
    except OperationalError:
        pass

    if isinstance(db, PostgresqlDatabase):
        with open("conf/auditing.sql", 'br') as input_file:
            sql = readup_file(input_file)
            with db.get_cursor() as cr:
                cr.execute(sql)


def drop_tables():
    """Drop all model tables."""
    for m in (Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, OrgInfo, OrgInvitation,
              OrcidApiCall, OrcidAuthorizeCall, Task, AffiliationRecord, Url, UserInvitation):
        if m.table_exists():
            try:
                m.drop_table(fail_silently=True, cascade=db.drop_cascade)
            except OperationalError:
                pass
