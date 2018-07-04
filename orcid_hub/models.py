# -*- coding: utf-8 -*-
"""Application models."""

import copy
import csv
import json
import os
import random
import re
import secrets
import string
import uuid
import validators
from collections import namedtuple
from datetime import datetime
from hashlib import md5
from io import StringIO
from itertools import zip_longest
from urllib.parse import urlencode

import yaml
from flask_login import UserMixin, current_user
from peewee import BooleanField as BooleanField_
from peewee import (JOIN, BlobField, CharField, DateTimeField, DeferredRelation, Field,
                    FixedCharField, ForeignKeyField, IntegerField, Model, OperationalError,
                    PostgresqlDatabase, SmallIntegerField, TextField, fn)
from playhouse.shortcuts import model_to_dict
from pycountry import countries
from pykwalify.core import Core
from pykwalify.errors import SchemaError
from peewee_validates import ModelValidator

from . import app, db

ENV = app.config["ENV"]
DEFAULT_COUNTRY = app.config["DEFAULT_COUNTRY"]
SCHEMA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "schemas"))

ORCID_ID_REGEX = re.compile(r"^([X\d]{4}-?){3}[X\d]{4}$")
PARTIAL_DATE_REGEX = re.compile(r"\d+([/\-]\d+){,2}")


AFFILIATION_TYPES = (
    "student",
    "education",
    "staff",
    "employment",
)

try:
    from enum import IntFlag
except ImportError:  # pragma: no cover
    from enum import IntEnum as IntFlag


class ModelException(Exception):
    """Applicaton model exception."""

    pass


def validate_orcid_id(value):
    """Validate ORCID iD (both format and the check-sum)."""
    if not value:
        return

    if not ORCID_ID_REGEX.match(value):
        raise ValueError(
            f"Invalid ORCID iD {value}. It should be in the form of 'xxxx-xxxx-xxxx-xxxx' where x is a digit."
        )
    check = 0
    for n in value:
        if n == '-':
            continue
        check = (2 * check + int(10 if n == 'X' else n)) % 11
    if check != 1:
        raise ValueError(f"Invalid ORCID iD {value} checksum. Make sure you have entered correct ORCID iD.")


def lazy_property(fn):
    """Make a property lazy-evaluated."""
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazy_property


class PartialDate(namedtuple("PartialDate", ["year", "month", "day"])):
    """Partial date (without month day or both month and month day."""

    def as_orcid_dict(self):
        """Return ORCID dictionary representation of the partial date."""
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
        2003-07-14

        >>> PartialDate.create("2003/03")
        2003-03

        >>> PartialDate.create("2003/07/14")
        2003-07-14

        >>> PartialDate.create("03/2003")
        2003-03

        >>> PartialDate.create("14/07/2003")
        2003-07-14
        """
        if value is None or value == {}:
            return None
        if isinstance(value, str):
            match = PARTIAL_DATE_REGEX.search(value)
            if not match:
                raise ModelException(f"Wrong partial date value '{value}'")
            value0 = match[0]
            if '/' in value0:
                parts = value0.split('/')
                return cls(*[int(v) for v in (parts[::-1] if len(parts[-1]) > 2 else parts)])
            return cls(*[int(v) for v in value0.split('-')])

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
        if "max_length" not in kwargs:
            kwargs["max_length"] = 19
        super().__init__(*args, **kwargs)

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
    def get(cls, *query, **kwargs):
        """Get a single model instance."""
        if query and not kwargs and len(query) == 1 and isinstance(query[0], int):
            return super().get(id=query[0])
        return super().get(*query, **kwargs)

    @classmethod
    def model_class_name(cls):
        """Get the class name of the model."""
        return cls._meta.name

    def __to_dashes(self, o):
        """Replace '_' with '-' in the dict keys."""
        if isinstance(o, (list, tuple)):
            return [self.__to_dashes(e) for e in o]
        elif isinstance(o, dict):
            return {k.replace('_', '-'): self.__to_dashes(v) for k, v in o.items()}
        return o

    def to_dict(self,
                to_dashes=False,
                recurse=True,
                backrefs=False,
                only=None,
                exclude=None,
                seen=None,
                extra_attrs=None,
                fields_from_query=None,
                max_depth=None):
        """Get dictionary representation of the model."""
        o = model_to_dict(
            self,
            recurse=recurse,
            backrefs=backrefs,
            only=only,
            exclude=exclude,
            seen=seen,
            extra_attrs=extra_attrs,
            fields_from_query=fields_from_query,
            max_depth=max_depth)
        for k, v in o.items():
            if isinstance(v, PartialDate):
                o[k] = str(v)
        if to_dashes:
            return self.__to_dashes(o)
        return o

    def reload(self):
        """Refresh the object from the DB."""
        newer_self = self.get(self._meta.primary_key == self._get_pk_value())
        for field_name in self._meta.fields.keys():
            val = getattr(newer_self, field_name)
            setattr(self, field_name, val)
        self._dirty.clear()

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

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(null=True, default=None)

    # created_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)
    # updated_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)

    def save(self, *args, **kwargs):  # noqa: D102
        if self.is_dirty() and self._dirty != {"orcid_updated_at"}:
            self.updated_at = datetime.utcnow()
            if current_user and hasattr(current_user, "id"):
                if hasattr(self, "created_by") and self.created_by and hasattr(self, "updated_by"):
                    self.updated_by_id = current_user.id
                elif hasattr(self, "created_by"):
                    self.created_by_id = current_user.id
        return super().save(*args, **kwargs)


class File(BaseModel):
    """Uploaded image files."""

    filename = CharField(max_length=100)
    data = BlobField()
    mimetype = CharField(max_length=30, db_column="mime_type")
    token = FixedCharField(max_length=8, unique=True, default=lambda: secrets.token_urlsafe(8)[:8])


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
    else:  # pragma: no cover
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
        related_name="tech_contact_of",
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

    can_use_api = BooleanField(null=True, help_text="The organisation can access ORCID Hub API.")
    logo = ForeignKeyField(
        File, on_delete="CASCADE", null=True, help_text="The logo of the organisation")
    email_template = TextField(null=True)
    email_template_enabled = BooleanField(null=True, default=False)
    webhook_enabled = BooleanField(default=False, null=True)
    webhook_url = CharField(max_length=100, null=True)
    email_notifications_enabled = BooleanField(default=False, null=True)
    notification_email = CharField(max_length=100, null=True, verbose_name="Notification Email Address")

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

            if self.field_is_updated("tech_contact") and self.tech_contact:
                if not self.tech_contact.has_role(Role.TECHNICAL):
                    self.tech_contact.roles |= Role.TECHNICAL
                    self.tech_contact.save()
                    app.logger.info(f"Added TECHNICAL role to user {self.tech_contact}")

        super().save(*args, **kwargs)


class OrgInfo(BaseModel):
    """Preloaded organisation data."""

    name = CharField(max_length=100, unique=True, verbose_name="Organisation")
    tuakiri_name = CharField(max_length=100, unique=True, null=True, verbose_name="TUAKIRI Name")
    title = CharField(null=True, verbose_name="Contact Person Tile")
    first_name = CharField(null=True, verbose_name="Contact Person's First Name")
    last_name = CharField(null=True, verbose_name="Contact Person's Last Name")
    role = CharField(null=True, verbose_name="Contact Person's Role")
    email = CharField(null=True, verbose_name="Contact Person's Email Address")
    phone = CharField(null=True, verbose_name="Contact Person's Phone")
    is_public = BooleanField(
        null=True, default=False, help_text="Permission to post contact information to WEB")
    country = CharField(null=True, verbose_name="Country Code", default=DEFAULT_COUNTRY)
    city = CharField(null=True, verbose_name="City of Home Campus")
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
            # skip empty lines:
            if row is None or (len(row) == 1 and row[0].strip() == ''):
                continue

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
    email = CharField(max_length=120, unique=True, null=True, verbose_name="Email Address")
    eppn = CharField(max_length=120, unique=True, null=True, verbose_name="EPPN")
    # ORCiD:
    orcid = OrcidIdField(null=True, verbose_name="ORCID iD", help_text="User's ORCID iD")
    confirmed = BooleanField(default=False)
    # Role bit-map:
    roles = SmallIntegerField(default=0)

    is_locked = BooleanField(default=False)
    webhook_enabled = BooleanField(default=False, null=True)
    orcid_updated_at = DateTimeField(null=True, default=None)

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
        return (Organisation.select(
            Organisation, (Organisation.tech_contact_id == self.id).alias("is_tech_contact"),
            ((UserOrg.is_admin.is_null(False)) & (UserOrg.is_admin)).alias("is_admin")).join(
                UserOrg, on=((UserOrg.org_id == Organisation.id) & (UserOrg.user_id == self.id)))
                .naive())

    @property
    def linked_accounts(self):
        """Get all linked accounts - accounts sharing the same ORCID ID."""
        return [u for u in User.select().where(User.orcid == self.orcid)] if self.orcid else [self]

    @property
    def available_organisations(self):
        """Get all not yet linked to the user organisation query."""
        return (Organisation.select(Organisation).where(UserOrg.id.is_null()).join(
            UserOrg,
            JOIN.LEFT_OUTER,
            on=((UserOrg.org_id == Organisation.id) & (UserOrg.user_id == self.id))))

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
            self.roles &= ~Role.SUPERUSER

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

    def is_admin_of(self, org=None):
        """Indicats if the user is the technical contact of the organisation."""
        if org is None:
            org = self.organisation
        return org and UserOrg.select().where(UserOrg.user == self, UserOrg.org == org, UserOrg.is_admin).exists()

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
    email = TextField(
        help_text="The email address the invitation was sent to.",
        verbose_name="Invitee Email Address")
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
        null=True, default=False, help_text="User is an administrator for the organisation")

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

    user = ForeignKeyField(User, null=True, index=True)  # TODO: add validation for 3-legged authorization tokens
    org = ForeignKeyField(Organisation, index=True, verbose_name="Organisation")
    scope = TextField(null=True, db_column="scope")  # TODO impomenet property
    access_token = CharField(max_length=36, unique=True, null=True)
    issue_time = DateTimeField(default=datetime.utcnow)
    refresh_token = CharField(max_length=36, unique=True, null=True)
    expires_in = IntegerField(default=0)
    created_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)
    updated_by = ForeignKeyField(DeferredUser, on_delete="SET NULL", null=True)

    @property
    def scopes(self):  # noqa: D102
        if self.scope:
            return self.scope.split(',')
        return []

    @scopes.setter
    def scopes(self, value):  # noqa: D102
        if isinstance(value, str):
            self.scope = value
        else:
            self.scope = ','.join(value)


class UserOrgAffiliation(BaseModel, AuditMixin):
    """For Keeping the information about the affiliation."""

    user = ForeignKeyField(User)
    organisation = ForeignKeyField(Organisation, index=True, verbose_name="Organisation")
    disambiguated_id = CharField(verbose_name="Disambiguation ORG Id", null=True)
    disambiguation_source = CharField(verbose_name="Disambiguation ORG Source", null=True)
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

    called_at = DateTimeField(default=datetime.utcnow)
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

    called_at = DateTimeField(default=datetime.utcnow)
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

    org = ForeignKeyField(
        Organisation, index=True, verbose_name="Organisation", on_delete="SET NULL")
    completed_at = DateTimeField(null=True)
    filename = TextField(null=True)
    created_by = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="created_tasks")
    updated_by = ForeignKeyField(
        User, on_delete="SET NULL", null=True, related_name="updated_tasks")
    task_type = SmallIntegerField(default=0)
    expires_at = DateTimeField(null=True)
    expiry_email_sent_at = DateTimeField(null=True)
    completed_count = TextField(null=True, help_text="gives the status of uploaded task")

    def __repr__(self):
        return self.filename or f"{TaskType(self.task_type).name.capitalize()} record processing task #{self.id}"

    @property
    def is_expiry_email_sent(self):
        """Test if the expiry email is sent ot not."""
        return bool(self.expiry_email_sent_at)

    @lazy_property
    def record_count(self):
        """Get count of the loaded recoreds."""
        return self.records.count()

    @property
    def record_model(self):
        """Get record model class."""
        _, models = self.records.get_query_meta()
        model, = models.keys()
        return model

    @lazy_property
    def records(self):
        """Get all task record query."""
        return getattr(self, TaskType(self.task_type).name.lower() + "_records")

    @property
    def error_count(self):
        """Get error count encountered during processing batch task."""
        q = self.records
        _, models = q.get_query_meta()
        model, = models.keys()
        return self.records.where(self.record_model.status ** "%error%").count()

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load affiliation record data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source)
        reader = csv.reader(source)
        header = next(reader)
        if filename is None:
            if hasattr(source, "name"):
                filename = source.name
            else:
                filename = datetime.utcnow().isoformat(timespec="seconds")

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
                       r"disambiguat.*source", r"put|code", "orcid.*", "external.*|.*identifier")
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
                    # skip empty lines:
                    if len(row) == 0:
                        continue
                    if len(row) == 1 and row[0].strip() == '':
                        continue

                    email = val(row, 2, "").lower()
                    orcid = val(row, 15)
                    external_id = val(row, 16)

                    if not email and not orcid and external_id and validators.email(external_id):
                        # if email is missing and exernal ID is given as a valid email, use it:
                        email = external_id

                    # The uploaded country must be from ISO 3166-1 alpha-2
                    country = val(row, 11)

                    if country:
                        try:
                            country = countries.lookup(country).alpha_2
                        except Exception:
                            raise ModelException(
                                f" (Country must be 2 character from ISO 3166-1 alpha-2) in the row "
                                f"#{row_no+2}: {row}. Header: {header}")

                    if not (email or orcid):
                        raise ModelException(
                            f"Missing user identifier (email address or ORCID iD) in the row "
                            f"#{row_no+2}: {row}. Header: {header}")

                    if orcid:
                        validate_orcid_id(orcid)

                    if not email or not validators.email(email):
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
                        country=country,
                        disambiguated_id=val(row, 12),
                        disambiguation_source=val(row, 13),
                        put_code=val(row, 14),
                        orcid=orcid,
                        external_id=external_id)
                    validator = ModelValidator(af)
                    if not validator.validate():
                        raise ModelException(f"Invalid record: {validator.errors}")
                    af.save()
            except Exception:
                db.rollback()
                app.logger.exception("Failed to load affiliation file.")
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


class RecordModel(BaseModel):
    """Commond model bits of the task records."""

    def save(self, *args, **kwargs):
        """Update related batch task when changing the record."""
        if self.is_dirty() and hasattr(self, "task"):
            self.task.updated_at = datetime.utcnow()
            self.task.save()
        return super().save(*args, **kwargs)

    def add_status_line(self, line):
        """Add a text line to the status for logging processing progress."""
        ts = datetime.utcnow().isoformat(timespec="seconds")
        self.status = (self.status + "\n" if self.status else '') + ts + ": " + line


class GroupIdRecord(RecordModel):
    """GroupID records."""

    type_choices = [('publisher', 'publisher'), ('institution', 'institution'), ('journal', 'journal'),
                    ('conference', 'conference'), ('newspaper', 'newspaper'), ('newsletter', 'newsletter'),
                    ('magazine', 'magazine'), ('peer-review service', 'peer-review service')]
    type_choices.sort(key=lambda e: e[1])
    type_choices.insert(0, ("", ""))
    put_code = IntegerField(null=True)
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")
    name = CharField(max_length=120,
                     help_text="The name of the group. This can be the name of a journal (Journal of Criminal Justice),"
                               " a publisher (Society of Criminal Justice), or non-specific description (Legal Journal)"
                               " as required.")
    group_id = CharField(max_length=120,
                         help_text="The group's identifier, formatted as type:identifier, e.g. issn:12345678. "
                                   "This can be as specific (e.g. the journal's ISSN) or vague as required. "
                                   "Valid types include: issn, ringgold, orcid-generated, fundref, publons.")
    description = CharField(max_length=120,
                            help_text="A brief textual description of the group. "
                                      "This can be as specific or vague as required.")
    type = CharField(max_length=80, choices=type_choices,
                     help_text="One of the specified types: publisher; institution; journal; conference; newspaper; "
                               "newsletter; magazine; peer-review service.")
    organisation = ForeignKeyField(
        Organisation, related_name="organisation", on_delete="CASCADE", null=True)

    class Meta:  # noqa: D101,D106
        db_table = "group_id_record"
        table_alias = "gid"


class AffiliationRecord(RecordModel):
    """Affiliation record loaded from CSV file for batch processing."""

    is_active = BooleanField(
        default=False, help_text="The record is marked 'active' for batch processing", null=True)
    task = ForeignKeyField(Task, related_name="affiliation_records", on_delete="CASCADE")
    put_code = IntegerField(null=True)
    external_id = CharField(
        max_length=100,
        null=True,
        verbose_name="External ID",
        help_text="Record identifier used in the data source system.")
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")
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
    country = CharField(null=True, verbose_name="Country", max_length=2)
    disambiguated_id = CharField(
        null=True, max_length=20, verbose_name="Disambiguated Organization Identifier")
    disambiguation_source = CharField(
        null=True, max_length=100, verbose_name="Disambiguation Source")

    class Meta:  # noqa: D101,D106
        db_table = "affiliation_record"
        table_alias = "ar"


class TaskType(IntFlag):
    """Enum used to represent Task type."""

    AFFILIATION = 0  # Affilation of employment/education
    FUNDING = 1  # Funding
    WORK = 2
    PEER_REVIEW = 3

    def __eq__(self, other):
        if isinstance(other, TaskType):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return (self.name == other or self.name == getattr(other, "name", None))

    def __hash__(self):
        return hash(self.name)


class FundingRecord(RecordModel):
    """Funding record loaded from Json file for batch processing."""

    task = ForeignKeyField(Task, related_name="funding_records", on_delete="CASCADE")
    title = CharField(max_length=255)
    translated_title = CharField(null=True, max_length=255)
    translated_title_language_code = CharField(null=True, max_length=10)
    type = CharField(max_length=255)
    organization_defined_type = CharField(null=True, max_length=255)
    short_description = CharField(null=True, max_length=4000)
    amount = CharField(null=True, max_length=255)
    currency = CharField(null=True, max_length=3)
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    org_name = CharField(null=True, max_length=255, verbose_name="Organisation Name")
    city = CharField(null=True, max_length=255)
    region = CharField(null=True, max_length=255)
    country = CharField(null=True, max_length=255)
    disambiguated_org_identifier = CharField(null=True, max_length=255)
    disambiguation_source = CharField(null=True, max_length=255)
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True)
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load_from_json(cls, source, filename=None, org=None):
        """Load data from json file or a string."""
        if isinstance(source, str):
            # import data from file based on its extension; either it is yaml or json
            funding_data_list = load_yaml_json(filename=filename, source=source)

            for funding_data in funding_data_list:
                validation_source_data = copy.deepcopy(funding_data)
                validation_source_data = del_none(validation_source_data)

                # Adding schema valdation for funding
                validator = Core(
                    source_data=validation_source_data,
                    schema_files=[os.path.join(SCHEMA_DIR, "funding_schema.yaml")])
                validator.validate(raise_exception=True)

            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                task = Task.create(org=org, filename=filename, task_type=TaskType.FUNDING)

                for funding_data in funding_data_list:

                    title = get_val(funding_data, "title", "title", "value")
                    translated_title = get_val(funding_data, "title", "translated-title", "value")
                    translated_title_language_code = get_val(funding_data, "title", "translated-title", "language-code")
                    type = funding_data.get("type")
                    organization_defined_type = get_val(funding_data, "organization-defined-type", "value")
                    short_description = funding_data.get("short-description")
                    amount = get_val(funding_data, "amount", "value")
                    currency = get_val(funding_data, "amount", "currency-code")
                    start_date = PartialDate.create(funding_data.get("start-date"))
                    end_date = PartialDate.create(funding_data.get("end-date"))
                    org_name = get_val(funding_data, "organization", "name")
                    city = get_val(funding_data, "organization", "address", "city")
                    region = get_val(funding_data, "organization", "address", "region")
                    country = get_val(funding_data, "organization", "address", "country")
                    disambiguated_org_identifier = get_val(funding_data, "organization", "disambiguated-organization",
                                                           "disambiguated-organization-identifier")
                    disambiguation_source = get_val(funding_data, "organization", "disambiguated-organization",
                                                    "disambiguation-source")

                    funding_record = FundingRecord.create(
                        task=task,
                        title=title,
                        translated_title=translated_title,
                        translated_title_language_code=translated_title_language_code,
                        type=type,
                        organization_defined_type=organization_defined_type,
                        short_description=short_description,
                        amount=amount,
                        currency=currency,
                        org_name=org_name,
                        city=city,
                        region=region,
                        country=country,
                        disambiguated_org_identifier=disambiguated_org_identifier,
                        disambiguation_source=disambiguation_source,
                        start_date=start_date,
                        end_date=end_date)

                    invitees_list = funding_data.get("invitees") if funding_data.get("invitees") else None
                    if invitees_list:
                        for invitee in invitees_list:
                            identifier = invitee.get("identifier")
                            email = invitee.get("email")
                            first_name = invitee.get("first-name")
                            last_name = invitee.get("last-name")
                            orcid_id = invitee.get("ORCID-iD")
                            put_code = invitee.get("put-code")
                            visibility = invitee.get("visibility")

                            FundingInvitees.create(
                                funding_record=funding_record,
                                identifier=identifier,
                                email=email.lower(),
                                first_name=first_name,
                                last_name=last_name,
                                orcid=orcid_id,
                                visibility=visibility,
                                put_code=put_code)
                    else:
                        raise SchemaError(u"Schema validation failed:\n - "
                                          u"Expecting Invitees for which the funding record will be written")

                    contributors_list = funding_data.get("contributors").get("contributor") if \
                        funding_data.get("contributors") else None
                    if contributors_list:
                        for contributor in contributors_list:
                            orcid_id = get_val(contributor, "contributor-orcid", "path")
                            name = get_val(contributor, "credit-name", "value")
                            email = get_val(contributor, "contributor-email", "value")
                            role = get_val(contributor, "contributor-attributes", "contributor-role")

                            FundingContributor.create(
                                funding_record=funding_record,
                                orcid=orcid_id,
                                name=name,
                                email=email,
                                role=role)

                    external_ids_list = funding_data.get("external-ids").get("external-id") if \
                        funding_data.get("external-ids") else None
                    if external_ids_list:
                        for external_id in external_ids_list:
                            type = external_id.get("external-id-type")
                            value = external_id.get("external-id-value")
                            url = get_val(external_id, "external-id-url", "value")
                            relationship = external_id.get("external-id-relationship")
                            ExternalId.create(
                                funding_record=funding_record,
                                type=type,
                                value=value,
                                url=url,
                                relationship=relationship)
                    else:
                        raise SchemaError(u"Schema validation failed:\n - An external identifier is required")
                return task

            except Exception:
                db.rollback()
                app.logger.exception("Failed to load funding file.")
                raise

    class Meta:  # noqa: D101,D106
        db_table = "funding_record"
        table_alias = "fr"


class PeerReviewRecord(RecordModel):
    """Peer Review record loaded from Json file for batch processing."""

    task = ForeignKeyField(Task, related_name="peer_review_records", on_delete="CASCADE")
    review_group_id = CharField(max_length=255)
    reviewer_role = CharField(null=True, max_length=255)
    review_url = CharField(null=True, max_length=255)
    review_type = CharField(null=True, max_length=255)
    review_completion_date = PartialDateField(null=True)
    subject_external_id_type = CharField(null=True, max_length=255)
    subject_external_id_value = CharField(null=True, max_length=255)
    subject_external_id_url = CharField(null=True, max_length=255)
    subject_external_id_relationship = CharField(null=True, max_length=255)
    subject_container_name = CharField(null=True, max_length=255)
    subject_type = CharField(null=True, max_length=80)
    subject_name_title = CharField(null=True, max_length=255)
    subject_name_subtitle = CharField(null=True, max_length=255)
    subject_name_translated_title_lang_code = CharField(null=True, max_length=10)
    subject_name_translated_title = CharField(null=True, max_length=255)
    subject_url = CharField(null=True, max_length=255)
    convening_org_name = CharField(null=True, max_length=255)
    convening_org_city = CharField(null=True, max_length=255)
    convening_org_region = CharField(null=True, max_length=255)
    convening_org_country = CharField(null=True, max_length=255)
    convening_org_disambiguated_identifier = CharField(null=True, max_length=255)
    convening_org_disambiguation_source = CharField(null=True, max_length=255)
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True)
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load_from_json(cls, source, filename=None, org=None):
        """Load data from JSON file or a string."""
        if isinstance(source, str):
            # import data from file based on its extension; either it is yaml or json
            peer_review_data_list = load_yaml_json(filename=filename, source=source)

            for peer_review_data in peer_review_data_list:
                validation_source_data = copy.deepcopy(peer_review_data)
                validation_source_data = del_none(validation_source_data)

                validator = Core(
                    source_data=validation_source_data,
                    schema_files=[os.path.join(SCHEMA_DIR, "peer_review_schema.yaml")])
                validator.validate(raise_exception=True)

            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                task = Task.create(org=org, filename=filename, task_type=TaskType.PEER_REVIEW)

                for peer_review_data in peer_review_data_list:

                    review_group_id = peer_review_data.get("review-group-id") if peer_review_data.get(
                        "review-group-id") else None

                    reviewer_role = peer_review_data.get("reviewer-role") if peer_review_data.get(
                        "reviewer-role") else None

                    review_url = peer_review_data.get("review-url").get("value") if peer_review_data.get(
                        "review-url") else None

                    review_type = peer_review_data.get("review-type") if peer_review_data.get("review-type") else None

                    review_completion_date = PartialDate.create(peer_review_data.get("review-completion-date"))

                    subject_external_id_type = peer_review_data.get("subject-external-identifier").get(
                        "external-id-type") if peer_review_data.get(
                        "subject-external-identifier") else None

                    subject_external_id_value = peer_review_data.get("subject-external-identifier").get(
                        "external-id-value") if peer_review_data.get(
                        "subject-external-identifier") else None

                    subject_external_id_url = peer_review_data.get("subject-external-identifier").get(
                        "external-id-url").get("value") if peer_review_data.get(
                        "subject-external-identifier") and peer_review_data.get("subject-external-identifier").get(
                        "external-id-url") else None

                    subject_external_id_relationship = peer_review_data.get("subject-external-identifier").get(
                        "external-id-relationship") if peer_review_data.get(
                        "subject-external-identifier") else None

                    subject_container_name = peer_review_data.get("subject-container-name").get(
                        "value") if peer_review_data.get(
                        "subject-container-name") else None

                    subject_type = peer_review_data.get("subject-type") if peer_review_data.get(
                        "subject-type") else None

                    subject_name_title = peer_review_data.get("subject-name").get("title").get(
                        "value") if peer_review_data.get(
                        "subject-name") and peer_review_data.get("subject-name").get("title") else None

                    subject_name_subtitle = peer_review_data.get("subject-name").get("subtitle").get(
                        "value") if peer_review_data.get(
                        "subject-name") and peer_review_data.get("subject-name").get("subtitle") else None

                    subject_name_translated_title_lang_code = peer_review_data.get("subject-name").get(
                        "translated-title").get(
                        "language-code") if peer_review_data.get(
                        "subject-name") and peer_review_data.get("subject-name").get("translated-title") else None

                    subject_name_translated_title = peer_review_data.get("subject-name").get(
                        "translated-title").get(
                        "value") if peer_review_data.get(
                        "subject-name") and peer_review_data.get("subject-name").get("translated-title") else None

                    subject_url = peer_review_data.get("subject-url").get("value") if peer_review_data.get(
                        "subject-name") else None

                    convening_org_name = peer_review_data.get("convening-organization").get(
                        "name") if peer_review_data.get(
                        "convening-organization") else None

                    convening_org_city = peer_review_data.get("convening-organization").get("address").get(
                        "city") if peer_review_data.get("convening-organization") and peer_review_data.get(
                        "convening-organization").get("address") else None

                    convening_org_region = peer_review_data.get("convening-organization").get("address").get(
                        "region") if peer_review_data.get("convening-organization") and peer_review_data.get(
                        "convening-organization").get("address") else None

                    convening_org_country = peer_review_data.get("convening-organization").get("address").get(
                        "country") if peer_review_data.get("convening-organization") and peer_review_data.get(
                        "convening-organization").get("address") else None

                    convening_org_disambiguated_identifier = peer_review_data.get(
                        "convening-organization").get("disambiguated-organization").get(
                        "disambiguated-organization-identifier") if peer_review_data.get(
                        "convening-organization") and peer_review_data.get("convening-organization").get(
                        "disambiguated-organization") else None

                    convening_org_disambiguation_source = peer_review_data.get(
                        "convening-organization").get("disambiguated-organization").get(
                        "disambiguation-source") if peer_review_data.get(
                        "convening-organization") and peer_review_data.get("convening-organization").get(
                        "disambiguated-organization") else None

                    peer_review_record = PeerReviewRecord.create(
                        task=task,
                        review_group_id=review_group_id,
                        reviewer_role=reviewer_role,
                        review_url=review_url,
                        review_type=review_type,
                        review_completion_date=review_completion_date,
                        subject_external_id_type=subject_external_id_type,
                        subject_external_id_value=subject_external_id_value,
                        subject_external_id_url=subject_external_id_url,
                        subject_external_id_relationship=subject_external_id_relationship,
                        subject_container_name=subject_container_name,
                        subject_type=subject_type,
                        subject_name_title=subject_name_title,
                        subject_name_subtitle=subject_name_subtitle,
                        subject_name_translated_title_lang_code=subject_name_translated_title_lang_code,
                        subject_name_translated_title=subject_name_translated_title,
                        subject_url=subject_url,
                        convening_org_name=convening_org_name,
                        convening_org_city=convening_org_city,
                        convening_org_region=convening_org_region,
                        convening_org_country=convening_org_country,
                        convening_org_disambiguated_identifier=convening_org_disambiguated_identifier,
                        convening_org_disambiguation_source=convening_org_disambiguation_source)

                    invitees_list = peer_review_data.get("invitees") if peer_review_data.get("invitees") else None

                    if invitees_list:
                        for invitee in invitees_list:
                            identifier = invitee.get("identifier") if invitee.get("identifier") else None
                            email = invitee.get("email") if invitee.get("email") else None
                            first_name = invitee.get("first-name") if invitee.get("first-name") else None
                            last_name = invitee.get("last-name") if invitee.get("last-name") else None
                            orcid_id = invitee.get("ORCID-iD") if invitee.get("ORCID-iD") else None
                            put_code = invitee.get("put-code") if invitee.get("put-code") else None
                            visibility = get_val(invitee, "visibility")

                            PeerReviewInvitee.create(
                                peer_review_record=peer_review_record,
                                identifier=identifier,
                                email=email.lower(),
                                first_name=first_name,
                                last_name=last_name,
                                orcid=orcid_id,
                                visibility=visibility,
                                put_code=put_code)
                    else:
                        raise SchemaError(u"Schema validation failed:\n - "
                                          u"Expecting Invitees for which the peer review record will be written")

                    external_ids_list = peer_review_data.get("review-identifiers").get("external-id") if \
                        peer_review_data.get("review-identifiers") else None
                    if external_ids_list:
                        for external_id in external_ids_list:
                            type = external_id.get("external-id-type")
                            value = external_id.get("external-id-value")
                            url = external_id.get("external-id-url").get("value") if \
                                external_id.get("external-id-url") else None
                            relationship = external_id.get("external-id-relationship")
                            PeerReviewExternalId.create(
                                peer_review_record=peer_review_record,
                                type=type,
                                value=value,
                                url=url,
                                relationship=relationship)
                    else:
                        raise SchemaError(u"Schema validation failed:\n - An external identifier is required")

                return task
            except Exception:
                db.rollback()
                app.logger.exception("Failed to load peer review file.")
                raise

    class Meta:  # noqa: D101,D106
        db_table = "peer_review_record"
        table_alias = "pr"


class WorkRecord(RecordModel):
    """Work record loaded from Json file for batch processing."""

    task = ForeignKeyField(Task, related_name="work_records", on_delete="CASCADE")
    title = CharField(max_length=255)
    sub_title = CharField(null=True, max_length=255)
    translated_title = CharField(null=True, max_length=255)
    translated_title_language_code = CharField(null=True, max_length=10)
    journal_title = CharField(null=True, max_length=255)
    short_description = CharField(null=True, max_length=4000)
    citation_type = CharField(max_length=255)
    citation_value = CharField(max_length=255)
    type = CharField(null=True, max_length=255)
    publication_date = PartialDateField(null=True)
    publication_media_type = CharField(null=True, max_length=255)
    url = CharField(null=True, max_length=255)
    language_code = CharField(null=True, max_length=10)
    country = CharField(null=True, max_length=255)

    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True)
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load_from_json(cls, source, filename=None, org=None):
        """Load data from JSON file or a string."""
        if isinstance(source, str):
            # import data from file based on its extension; either it is yaml or json
            work_data_list = load_yaml_json(filename=filename, source=source)

            # TODO: validation of uploaded work file
            for work_data in work_data_list:
                validation_source_data = copy.deepcopy(work_data)
                validation_source_data = del_none(validation_source_data)

                # Adding schema valdation for Work
                validator = Core(
                    source_data=validation_source_data,
                    schema_files=[os.path.join(SCHEMA_DIR, "work_schema.yaml")])
                validator.validate(raise_exception=True)

            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                task = Task.create(org=org, filename=filename, task_type=TaskType.WORK)

                for work_data in work_data_list:

                    title = get_val(work_data, "title", "title", "value")
                    sub_title = get_val(work_data, "title", "subtitle", "value")
                    translated_title = get_val(work_data, "title", "translated-title", "value")
                    translated_title_language_code = get_val(work_data, "title", "translated-title", "language-code")
                    journal_title = get_val(work_data, "journal-title", "value")
                    short_description = get_val(work_data, "short-description")
                    citation_type = get_val(work_data, "citation", "citation-type")
                    citation_value = get_val(work_data, "citation", "citation-value")
                    type = get_val(work_data, "type")
                    publication_media_type = get_val(work_data, "publication-date", "media-type")
                    url = get_val(work_data, "url", "value")
                    language_code = get_val(work_data, "language-code")
                    country = get_val(work_data, "country", "value")

                    # Removing key 'media-type' from the publication_date dict. and only considering year, day & month
                    publication_date = PartialDate.create(
                        {date_key: work_data.get("publication-date")[date_key] for date_key in
                         ('day', 'month', 'year')}) if work_data.get("publication-date") else None

                    work_record = WorkRecord.create(
                        task=task,
                        title=title,
                        sub_title=sub_title,
                        translated_title=translated_title,
                        translated_title_language_code=translated_title_language_code,
                        journal_title=journal_title,
                        short_description=short_description,
                        citation_type=citation_type,
                        citation_value=citation_value,
                        type=type,
                        publication_date=publication_date,
                        publication_media_type=publication_media_type,
                        url=url,
                        language_code=language_code,
                        country=country)

                    invitees_list = work_data.get("invitees") if work_data.get("invitees") else None

                    if invitees_list:
                        for invitee in invitees_list:
                            identifier = invitee.get("identifier")
                            email = invitee.get("email")
                            first_name = invitee.get("first-name")
                            last_name = invitee.get("last-name")
                            orcid_id = invitee.get("ORCID-iD")
                            put_code = invitee.get("put-code")
                            visibility = get_val(invitee, "visibility")

                            WorkInvitees.create(
                                work_record=work_record,
                                identifier=identifier,
                                email=email.lower(),
                                first_name=first_name,
                                last_name=last_name,
                                orcid=orcid_id,
                                visibility=visibility,
                                put_code=put_code)
                    else:
                        raise SchemaError(u"Schema validation failed:\n - "
                                          u"Expecting Invitees for which the work record will be written")

                    contributors_list = work_data.get("contributors").get("contributor") if \
                        work_data.get("contributors") else None

                    if contributors_list:
                        for contributor in contributors_list:
                            orcid_id = get_val(contributor, "contributor-orcid", "path")
                            name = get_val(contributor, "credit-name", "value")
                            email = get_val(contributor, "contributor-email", "value")
                            role = get_val(contributor, "contributor-attributes", "contributor-role")
                            contributor_sequence = get_val(contributor, "contributor-attributes",
                                                           "contributor-sequence")

                            WorkContributor.create(
                                work_record=work_record,
                                orcid=orcid_id,
                                name=name,
                                email=email,
                                role=role,
                                contributor_sequence=contributor_sequence)

                    external_ids_list = work_data.get("external-ids").get("external-id") if \
                        work_data.get("external-ids") else None
                    if external_ids_list:
                        for external_id in external_ids_list:
                            type = external_id.get("external-id-type")
                            value = external_id.get("external-id-value")
                            url = get_val(external_id, "external-id-url", "value")
                            relationship = external_id.get("external-id-relationship")
                            WorkExternalId.create(
                                work_record=work_record,
                                type=type,
                                value=value,
                                url=url,
                                relationship=relationship)
                    else:
                        raise SchemaError(u"Schema validation failed:\n - An external identifier is required")

                return task
            except Exception:
                db.rollback()
                app.logger.exception("Failed to load work record file.")
                raise

    class Meta:  # noqa: D101,D106
        db_table = "work_record"
        table_alias = "wr"


class ContributorModel(BaseModel):
    """Common model bits of the contributor records."""

    orcid = OrcidIdField(null=True)
    name = CharField(max_length=120, null=True)
    role = CharField(max_length=120, null=True)
    email = CharField(max_length=120, null=True)


class WorkContributor(ContributorModel):
    """Researcher or contributor - related to work."""

    work_record = ForeignKeyField(
        WorkRecord, related_name="work_contributors", on_delete="CASCADE")
    contributor_sequence = CharField(max_length=120, null=True)

    class Meta:  # noqa: D101,D106
        db_table = "work_contributor"
        table_alias = "wc"


class FundingContributor(ContributorModel):
    """Researcher or contributor - reciever of the funding."""

    funding_record = ForeignKeyField(
        FundingRecord, related_name="contributors", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        db_table = "funding_contributor"
        table_alias = "fc"


class InviteesModel(BaseModel):
    """Common model bits of the invitees records."""

    identifier = CharField(max_length=120, null=True)
    email = CharField(max_length=120, null=True)
    first_name = CharField(max_length=120, null=True)
    last_name = CharField(max_length=120, null=True)
    orcid = OrcidIdField(null=True)
    put_code = IntegerField(null=True)
    visibility = CharField(null=True, max_length=100)
    status = TextField(null=True, help_text="Record processing status.")
    processed_at = DateTimeField(null=True)

    def add_status_line(self, line):
        """Add a text line to the status for logging processing progress."""
        ts = datetime.utcnow().isoformat(timespec="seconds")
        self.status = (self.status + "\n" if self.status else '') + ts + ": " + line


class PeerReviewInvitee(InviteesModel):
    """Researcher or Invitee - related to peer review."""

    peer_review_record = ForeignKeyField(
        PeerReviewRecord, related_name="peer_review_invitee", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        db_table = "peer_review_invitee"
        table_alias = "pi"


class WorkInvitees(InviteesModel):
    """Researcher or Invitees - related to work."""

    work_record = ForeignKeyField(
        WorkRecord, related_name="work_invitees", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        db_table = "work_invitees"
        table_alias = "wi"


class FundingInvitees(InviteesModel):
    """Researcher or Invitees - related to funding."""

    funding_record = ForeignKeyField(
        FundingRecord, related_name="funding_invitees", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        db_table = "funding_invitees"
        table_alias = "fi"


class ExternalIdModel(BaseModel):
    """Common model bits of the ExternalId records."""

    type = CharField(max_length=255)
    value = CharField(max_length=255)
    url = CharField(max_length=200, null=True)
    relationship = CharField(max_length=255, null=True)


class WorkExternalId(ExternalIdModel):
    """Work ExternalId loaded for batch processing."""

    work_record = ForeignKeyField(
        WorkRecord, related_name="external_ids", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        db_table = "work_external_id"
        table_alias = "wei"


class PeerReviewExternalId(ExternalIdModel):
    """Peer Review ExternalId loaded for batch processing."""

    peer_review_record = ForeignKeyField(
        PeerReviewRecord, related_name="external_ids", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        db_table = "peer_review_external_id"
        table_alias = "pei"


class ExternalId(ExternalIdModel):
    """Funding ExternalId loaded for batch processing."""

    funding_record = ForeignKeyField(
        FundingRecord, related_name="external_ids", on_delete="CASCADE")

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


class Client(BaseModel, AuditMixin):
    """API Client Application/Consumer.

    A client is the app which wants to use the resource of a user.
    It is suggested that the client is registered by a user on your site,
    but it is not required.
    """

    name = CharField(null=True, max_length=40, help_text="human readable name, not required")
    homepage_url = CharField(null=True, max_length=100)
    description = CharField(
        null=True, max_length=400, help_text="human readable description, not required")
    user = ForeignKeyField(
        User, null=True, on_delete="SET NULL", help_text="creator of the client, not required")
    org = ForeignKeyField(Organisation, on_delete="CASCADE", related_name="client_applications")

    client_id = CharField(max_length=100, unique=True)
    client_secret = CharField(max_length=55, unique=True)
    is_confidential = BooleanField(null=True, help_text="public or confidential")
    grant_type = CharField(max_length=18, default="client_credentials", null=True)
    response_type = CharField(max_length=4, default="code", null=True)

    _redirect_uris = TextField(null=True)
    _default_scopes = TextField(null=True)

    def save(self, *args, **kwargs):  # noqa: D102
        if self.is_dirty() and self.user_id is None and current_user:
            self.user_id = current_user.id
        return super().save(*args, **kwargs)

    @property
    def client_type(self):  # noqa: D102
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):  # noqa: D102
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @redirect_uris.setter
    def redirect_uris(self, value):
        if value and isinstance(value, str):
            self._redirect_uris = value

    @property
    def callback_urls(self):  # noqa: D102
        return self._redirect_uris

    @callback_urls.setter
    def callback_urls(self, value):
        self._redirect_uris = value

    @property
    def default_redirect_uri(self):  # noqa: D102
        ru = self.redirect_uris
        if not ru:
            return None
        return self.redirect_uris[0]

    @property
    def default_scopes(self):  # noqa: D102
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    def validate_scopes(self, scopes):
        """Validate client requested scopes."""
        return "/webhook" in scopes or not scopes

    def __repr__(self):  # noqa: D102
        return self.name or self.homepage_url or self.description


class Grant(BaseModel):
    """Grant Token / Authorization Code.

    A grant token is created in the authorization flow, and will be destroyed when
    the authorization is finished. In this case, it would be better to store the data
    in a cache, which leads to better performance.
    """

    user = ForeignKeyField(User, on_delete="CASCADE")

    # client_id = db.Column(
    #     db.String(40), db.ForeignKey('client.client_id'),
    #     nullable=False,
    # )
    client = ForeignKeyField(Client, index=True)
    code = CharField(max_length=255, index=True)

    redirect_uri = CharField(max_length=255, null=True)
    expires = DateTimeField(null=True)

    _scopes = TextField(null=True)

    # def delete(self):
    #     super().delete().execute()
    #     return self

    @property
    def scopes(self):  # noqa: D102
        if self._scopes:
            return self._scopes.split()
        return []

    @scopes.setter
    def scopes(self, value):  # noqa: D102
        if isinstance(value, str):
            self._scopes = value
        else:
            self._scopes = ' '.join(value)


class Token(BaseModel):
    """Bearer Token.

    A bearer token is the final token that could be used by the client.
    There are other token types, but bearer token is widely used.
    Flask-OAuthlib only comes with a bearer token.
    """

    client = ForeignKeyField(Client)
    user = ForeignKeyField(User, null=True, on_delete="SET NULL")
    token_type = CharField(max_length=40)

    access_token = CharField(max_length=100, unique=True)
    refresh_token = CharField(max_length=100, unique=True, null=True)
    expires = DateTimeField(null=True)
    _scopes = TextField(null=True)

    @property
    def scopes(self):  # noqa: D102
        if self._scopes:
            return self._scopes.split()
        return []

    @property
    def expires_at(self):  # noqa: D102
        return self.expires


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
            File,
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
            GroupIdRecord,
            OrgInvitation,
            Url,
            UserInvitation,
            FundingRecord,
            WorkRecord,
            WorkContributor,
            WorkExternalId,
            WorkInvitees,
            FundingContributor,
            FundingInvitees,
            ExternalId,
            PeerReviewRecord,
            PeerReviewInvitee,
            PeerReviewExternalId,
            Client,
            Grant,
            Token,
    ]:

        if not model.table_exists():
            model.create_table()


def create_audit_tables():
    """Create all DB audit tables for PostgreSQL DB."""
    try:
        db.connect()
    except OperationalError:
        pass

    if isinstance(db, PostgresqlDatabase):
        with open(os.path.join(os.path.dirname(__file__), "sql", "auditing.sql"), 'br') as input_file:
            sql = readup_file(input_file)
            db.commit()
            with db.get_cursor() as cr:
                cr.execute(sql)
            db.commit()


def drop_tables():
    """Drop all model tables."""
    for m in (Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, OrgInfo, OrgInvitation,
              OrcidApiCall, OrcidAuthorizeCall, Task, AffiliationRecord, Url, UserInvitation):
        if m.table_exists():
            try:
                m.drop_table(fail_silently=True, cascade=m._meta.database.drop_cascade)
            except OperationalError:
                pass


def load_yaml_json(filename, source):
    """Create a common way of loading json or yaml file."""
    if os.path.splitext(filename)[1][1:] == "yaml" or os.path.splitext(
            filename)[1][1:] == "yml":
        data_list = yaml.load(source)
    else:
        data_list = json.loads(source)

    # Removing None for correct schema validation
    if not isinstance(data_list, list):
        raise SchemaError(
            u"Schema validation failed:\n - Expecting a list of Records")
    return data_list


def del_none(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.

    So that the schema validation will not fail, for elements that are none
    """
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    del_none(item)
        elif isinstance(value, dict):
            del_none(value)
    return d


def get_val(d, *keys, default=None):
    """To get the value from uploaded fields."""
    for k in keys:
        if not d:
            break
        d = d.get(k, default)
    return d
