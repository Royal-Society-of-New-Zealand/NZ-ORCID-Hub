# -*- coding: utf-8 -*-
"""Application models."""

import csv
import re
import uuid
from collections import namedtuple
from hashlib import md5
from io import StringIO
from itertools import zip_longest
from os import environ
from urllib.parse import urlencode

from flask_login import UserMixin, current_user
from peewee import (BooleanField, CharField, CompositeKey, DateTimeField, DeferredRelation, Field,
                    ForeignKeyField, IntegerField, Model, OperationalError, SmallIntegerField,
                    TextField, datetime)
from pycountry import countries

from application import db
from config import DEFAULT_COUNTRY

ENV = environ.get("ENV", "test")

try:
    from enum import IntFlag
except ImportError:
    from enum import IntEnum as IntFlag


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
    def create(cls, dict_value):
        """Create a partial date form ORCID dictionary representation.

        >>> PartialDate.create({"year": {"value": "2003"}}).as_orcid_dict()
        {'year': {'value': '2003'}, 'month': None, 'day': None}

        >>> PartialDate.create({"year": {"value": "2003"}}).year
        2003
        """
        if dict_value is None or dict_value == {}:
            return None
        return cls(**{k: int(v.get("value")) if v else None for k, v in dict_value.items()})

    def as_datetime(self):
        return datetime.datetime(self.year, self.month, self.day)


PartialDate.__new__.__defaults__ = (None, ) * len(PartialDate._fields)


class PartialDateField(Field):
    """Partial date custom DB data field mapped to varchar(10)."""

    db_field = 'varchar(10)'

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
        return PartialDate(**dict(zip_longest(("year", "month", "day", ), parts)))


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
    class Meta:
        database = db


class AuditMixin(Model):

    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super().save(*args, **kwargs)


DeferredUser = DeferredRelation()


class Organisation(BaseModel, AuditMixin):
    """
    Research oranisation
    """
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
    disambiguation_org_id = CharField(null=True)
    disambiguation_org_source = CharField(null=True)
    is_email_confirmed = BooleanField(default=False)
    tech_contact = ForeignKeyField(
        DeferredUser,
        related_name="tech_contact_for",
        on_delete="SET NULL",
        null=True,
        help_text="Organisation technical contact")

    @property
    def users(self):
        """
        Organisation's users (query)
        """
        return User.select().join(
            self.userorg_set.alias("sq"), on=(self.userorg_set.c.user_id == User.id))

    @property
    def admins(self):
        """Organisation's adminstrators (query)."""
        return User.select().join(
            self.userorg_set.where(self.userorg_set.c.is_admin).alias("sq"),
            on=(self.userorg_set.c.user_id == User.id))

    def __repr__(self):
        return self.name or self.tuakiri_name

    def save(self, *args, **kwargs):
        """Handle data saving."""
        if self.name is None:
            self.name = self.tuakiri_name

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
    disambiguation_org_id = CharField(
        null=True, verbose_name="common:disambiguated-organization-identifier")
    disambiguation_source = CharField(null=True, verbose_name="common:disambiguation-source")

    def __repr__(self):
        """String representation of the model."""
        return self.name or self.disambiguation_org_id or super().__repr__()

    class Meta:
        db_table = "org_info"
        table_alias = "oi"

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

        def val(row, i):
            if idxs[i] is None:
                return None
            else:
                v = row[idxs[i]].strip()
                return None if v == '' else v

        for row in reader:
            name = val(row, 0)
            oi, _ = OrgInfo.get_or_create(name=name)

            oi.title = val(row, 1)
            oi.first_name = val(row, 2)
            oi.last_name = val(row, 3)
            oi.role = val(row, 4)
            oi.email = val(row, 5)
            oi.phone = val(row, 6)
            oi.is_public = val(row, 7) and val(row, 7).upper() == "YES"
            oi.country = val(row, 8) or DEFAULT_COUNTRY
            oi.city = val(row, 9)
            oi.disambiguation_org_id = val(row, 10)
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
    orcid = CharField(max_length=120, verbose_name="ORCID", null=True)
    confirmed = BooleanField(default=False)
    # Role bit-map:
    roles = SmallIntegerField(default=0)

    is_locked = BooleanField(default=False)

    # TODO: many-to-many
    # NB! depricated!
    # TODO: we still need to rememeber the rognanistiaon that last authenticated the user
    organisation = ForeignKeyField(
        Organisation, related_name="members", on_delete="CASCADE", null=True)

    def __repr__(self):
        if self.name and (self.eppn or self.email):
            return "%s (%s)" % (self.name, self.email or self.eppn)
        return self.name or self.email or self.orcid or super().__repr__()

    @property
    def organisations(self):
        """
        All linked to the user organisation query
        """
        return Organisation.select().join(
            self.userorg_set.alias("sq"), on=Organisation.id == self.userorg_set.c.org_id)

    @property
    def admin_for(self):
        """
        Organisations the user is admin for (query)
        """
        return Organisation.select().join(
            self.userorg_set.where(self.userorg_set.c.is_admin).alias("sq"),
            on=Organisation.id == self.userorg_set.c.org_id)

    @property
    def is_active(self):
        # TODO: confirmed - user that email is cunfimed either by IdP or by confirmation email
        # ins't the same as "is active"
        return self.confirmed

    def has_role(self, role):
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name, `Role` instance, or integer value"""
        if isinstance(role, Role):
            return role & Role(self.roles)
        elif isinstance(role, str):
            try:
                return Role[role.upper()] & Role(self.roles)
            except:
                False
        elif type(role) is int:
            return role & self.roles
        else:
            return False

    @property
    def is_superuser(self):
        return self.roles & Role.SUPERUSER

    @property
    def is_admin(self):
        return self.roles & Role.ADMIN

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
                if unscoped_affiliation & {"student", "alum"}:
                    edu_person_affiliation |= Affiliation.EDU
                user_org.affiliations = edu_person_affiliation
            user_org.save()

        return users

    @property
    def uuid(self):
        return uuid.uuid5(uuid.NAMESPACE_URL, "mailto:" + (self.email or self.eppn))


DeferredUser.set_model(User)


class OrgInvitation(BaseModel, AuditMixin):
    """Organisation invitation to on-board the Hub."""

    invitee = ForeignKeyField(User, on_delete="SET NULL", related_name="received_org_invitations")
    inviter = ForeignKeyField(User, on_delete="SET NULL", related_name="sent_org_invitations")
    org = ForeignKeyField(Organisation, on_delete="SET NULL", verbose_name="Organisation")
    email = TextField(help_text="The email address the invitation was sent to.")
    token = TextField(unique=True)
    confirmed_at = DateTimeField(null=True)

    @property
    def sent_at(self):
        return self.created_at

    class Meta:
        db_table = "org_invitation"


class UserOrg(BaseModel, AuditMixin):
    """Linking object for many-to-many relationship."""

    user = ForeignKeyField(User, on_delete="CASCADE")
    org = ForeignKeyField(
        Organisation, index=True, on_delete="CASCADE", verbose_name="Organisation")

    is_admin = BooleanField(
        default=False, help_text="User is an administrator for the organisation")

    # Affiliation bit-map:
    affiliations = SmallIntegerField(default=0, null=True, verbose_name="EDU Person Affiliations")

    # TODO: the access token should be either here or in a separate list
    # access_token = CharField(max_length=120, unique=True, null=True)

    class Meta:
        db_table = "user_org"
        table_alias = "oa"
        primary_key = CompositeKey("user", "org")


class OrcidToken(BaseModel, AuditMixin):
    """
    For Keeping Orcid token in the table.
    """

    user = ForeignKeyField(User)
    org = ForeignKeyField(Organisation, index=True, verbose_name="Organisation")
    scope = TextField(null=True)
    access_token = CharField(max_length=36, unique=True, null=True)
    issue_time = DateTimeField(default=datetime.datetime.now)
    refresh_token = CharField(max_length=36, unique=True, null=True)
    expires_in = SmallIntegerField(default=0)


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

    class Meta:
        db_table = "user_organisation_affiliation"
        table_alias = "oua"


class OrcidApiCall(BaseModel):
    """ORCID API call audit entry."""
    called_at = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(User)
    method = TextField()
    url = TextField()
    query_params = TextField(null=True)
    body = TextField(null=True)
    put_code = IntegerField(null=True)
    response = TextField(null=True)
    response_time_ms = IntegerField(null=True)

    class Meta:
        db_table = "orcid_api_call"


def create_tables():
    """Create all DB tables."""
    try:
        db.connect()
    except OperationalError:
        pass
    models = (Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, OrgInfo, OrcidApiCall,
              OrgInvitation)
    db.create_tables(models)


def drop_tables():
    """Drop all model tables."""

    for m in (Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, OrgInfo, OrcidApiCall,
              OrgInvitation):
        if m.table_exists():
            try:
                m.drop_table(fail_silently=True, cascade=db.drop_cascade)
            except OperationalError:
                pass
