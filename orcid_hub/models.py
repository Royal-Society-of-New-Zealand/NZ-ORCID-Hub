# -*- coding: utf-8 -*-
"""Application models."""

import copy
import csv
import os
import random
import re
import secrets
import string
import uuid
from collections import namedtuple
from datetime import datetime
from enum import IntEnum, IntFlag
from functools import lru_cache
from hashlib import md5
from io import StringIO
from itertools import groupby, zip_longest
from urllib.parse import urlencode

import chardet
import jsonschema
import validators
import yaml
from flask import json
from flask_login import UserMixin, current_user
from peewee import JOIN, BlobField
from peewee import BooleanField as BooleanField_
from peewee import (
    CharField,
    DateTimeField,
    DeferredForeignKey,
    Field,
    FixedCharField,
    ForeignKeyField,
    IntegerField,
    ManyToManyField,
    Model,
    OperationalError,
    PostgresqlDatabase,
    SmallIntegerField,
    SqliteDatabase,
    TextField,
    fn,
)
from peewee_validates import ModelValidator

# from playhouse.reflection import generate_models
from playhouse.shortcuts import model_to_dict
from pycountry import countries, currencies, languages
from pykwalify.core import Core
from pykwalify.errors import SchemaError

from . import app, cache, db, schemas

ENV = app.config["ENV"]
DEFAULT_COUNTRY = app.config["DEFAULT_COUNTRY"]
SCHEMA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "schemas")
)

ORCID_ID_REGEX = re.compile(r"^([X\d]{4}-?){3}[X\d]{4}$")
PARTIAL_DATE_REGEX = re.compile(r"\d+([/\-\.]\d+){,2}")


AFFILIATION_TYPES = [
    "student",
    "education",
    "staff",
    "employment",
    "distinction",
    "position",
    "invited-position",
    "qualification",
    "membership",
    "service",
]
DISAMBIGUATION_SOURCES = ["ROR", "RINGGOLD", "GRID", "FUNDREF", "ISNI"]
VISIBILITIES = ["public", "private", "registered-only", "limited"]
visibility_choices = [(v, v.replace("-", " ").title()) for v in VISIBILITIES]
EXTERNAL_ID_TYPES = [
    "agr",
    "ark",
    "arxiv",
    "asin",
    "asin-tld",
    "authenticusid",
    "bibcode",
    "cba",
    "cienciaiul",
    "cit",
    "ctx",
    "dnb",
    "doi",
    "eid",
    "ethos",
    "grant_number",
    "handle",
    "hir",
    "isbn",
    "issn",
    "jfm",
    "jstor",
    "kuid",
    "lccn",
    "lensid",
    "mr",
    "oclc",
    "ol",
    "osti",
    "other-id",
    "pat",
    "pdb",
    "pmc",
    "pmid",
    "proposal-id",
    "rfc",
    "rrid",
    "source-work-id",
    "ssrn",
    "uri",
    "urn",
    "wosuid",
    "zbl",
]
FUNDING_TYPES = ["award", "contract", "grant", "salary-award"]
SUBJECT_TYPES = [
    "artistic-performance",
    "book",
    "book-chapter",
    "book-review",
    "conference-abstract",
    "conference-paper",
    "conference-poster",
    "data-set",
    "dictionary-entry",
    "disclosure",
    "dissertation",
    "edited-book",
    "encyclopedia-entry",
    "invention",
    "journal-article",
    "journal-issue",
    "lecture-speech",
    "license",
    "magazine-article",
    "manual",
    "newsletter-article",
    "newspaper-article",
    "online-resource",
    "other",
    "patent",
    "registered-copyright",
    "report",
    "research-technique",
    "research-tool",
    "spin-off-company",
    "standards-and-policy",
    "supervised-student-publication",
    "technical-standard",
    "test",
    "trademark",
    "translation",
    "undefined",
    "website",
    "working-paper",
]
REVIEWER_ROLES = ["chair", "editor", "member", "organizer", "reviewer"]
REVIEW_TYPES = ["evaluation", "review"]
review_type_choices = [(v, v.title()) for v in REVIEW_TYPES]
RELATIONSHIPS = ["part-of", "self", "version-of", "funded-by"]

WORK_TYPES = [
    # General Publications
    "book",
    "book-chapter",
    "conference-paper",
    "conference-output",  # apiv3.0
    "conference-presentation",  # apiv3.0
    "conference-poster",
    "conference-proceedings",  # apiv3.0
    "journal-article",
    "preprint",
    "dissertation-thesis",  # apiv3.0
    "working-paper",
    "other",

    # Reviews & Annotations
    "annotation",  # apiv3.0
    "book-review",
    "journal-issue",
    "review",  # apiv3.0
    "transcription",  # apiv3.0
    "translation",

    # Articles & Online Content
    "blog-post",  # apiv3.0
    "dictionary-entry",
    "encyclopedia-entry",
    "magazine-article",
    "newspaper-article",
    "report",
    "public-speech",
    "website",

    # Creative Works
    "artistic-performance",
    "design",  # apiv3.0
    "image",  # apiv3.0
    "online-resource",
    "moving-image",  # apiv3.0
    "musical-composition",  # apiv3.0
    "sound",  # apiv3.0

    # Research & Technical Data
    "cartographic-material",  # apiv3.0
    "clinical-study",  # apiv3.0
    "data-set",
    "data-management-plan",  # apiv3.0
    "physical-object",  # apiv3.0
    "research-technique",
    "research-tool",
    "software",

    # Intellectual Property
    "invention",
    "license",
    "patent",
    "registered-copyright",
    "standards-and-policy",
    "trademark",

    # Educational & Learning
    "lecture-speech",
    "learning-object",  # apiv3.0
    "supervised-student-publication",

    # Legacy Worktypes
    "conference-abstract",
    "disclosure",
    "edited-book",
    "manual",
    "newsletter-article",
    "spin-off-company",
    "technical-standards",
    "test",
]

WORK_TYPES = sorted(WORK_TYPES)

work_type_choices = [(v, v.replace("-", " ").title()) for v in WORK_TYPES]
CITATION_TYPES = [
    "bibtex",
    "formatted-apa",
    "formatted-chicago",
    "formatted-harvard",
    "formatted-ieee",
    "formatted-mla",
    "formatted-unspecified",
    "formatted-vancouver",
    "ris",
]
PROPERTY_TYPES = ["URL", "NAME", "KEYWORD", "COUNTRY"]
citation_type_choices = [(v, v.replace("-", " ").title()) for v in CITATION_TYPES]

country_choices = [(c.alpha_2, c.name) for c in countries]
country_choices.sort(key=lambda e: e[1])
language_choices = [(lang.alpha_2, lang.name) for lang in languages if hasattr(lang, "alpha_2")]
language_choices.sort(key=lambda e: e[1])
currency_choices = [(cur.alpha_3, cur.name) for cur in currencies]
currency_choices.sort(key=lambda e: e[1])
external_id_type_choices = [
    (v, v.replace("_", " ").replace("-", " ").title()) for v in EXTERNAL_ID_TYPES
]
relationship_choices = [(v, v.replace("-", " ").title()) for v in RELATIONSHIPS]
disambiguation_source_choices = [(v, v) for v in DISAMBIGUATION_SOURCES]
property_type_choices = [(v, v) for v in PROPERTY_TYPES]


class ModelExceptionError(Exception):
    """Application model exception."""

    pass


class NestedDict(dict):
    """Helper for traversing a nested dictionaries."""

    def get(self, *keys, default=None):
        """To get the value from uploaded fields."""
        d = self
        for k in keys:
            if d is default:
                break
            if not isinstance(d, dict):
                return default
            d = super(NestedDict, d).get(k, default)
        return d

    def get_orcid(self, *keys, default=None):
        """Get the ORCID iD value, sanize and validate it."""
        return validate_orcid_id(self.get(*keys, default=default))


def validate_orcid_id(value):
    """Sanitize and validate ORCID iD (both format and the check-sum)."""
    if not value:
        return

    if "/" in value:
        value = value.split("/")[-1]

    if not ORCID_ID_REGEX.match(value):
        raise ValueError(
            f"Invalid ORCID iD {value}. It should be in the form of 'xxxx-xxxx-xxxx-xxxx' where x is a digit."
        )
    check = 0
    for n in value:
        if n == "-":
            continue
        check = (2 * check + int(10 if n == "X" else n)) % 11
    if check != 1:
        raise ValueError(
            f"Invalid ORCID iD {value} checksum. Make sure you have entered correct ORCID iD."
        )

    return value


def lazy_property(fn):
    """Make a property lazy-evaluated."""
    attr_name = "_lazy_" + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy_property


def normalize_email(value):
    """Extact and normalize email value from the given raw data value, eg, 'Name <test@test.edu>'."""
    if value:
        value = value.strip().lower()
        return re.match(r"^(.*\<)?([^\>]*)\>?$", value).group(2) if "<" in value else value


class PartialDate(namedtuple("PartialDate", ["year", "month", "day"])):
    """Partial date (without month day or both month and month day."""

    def as_orcid_dict(self):
        """Return ORCID dictionary representation of the partial date."""
        if self.is_null:
            return None
        return dict(
            (
                (f, None if v is None else {"value": ("%04d" if f == "year" else "%02d") % v})
                for (f, v) in zip(self._fields, self)
            )
        )

    @property
    def is_null(self):
        """Test if if the date is undefined."""
        return self.year is None and self.month is None and self.day is None

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
                raise ModelExceptionError(f"Wrong partial date value '{value}'")
            value0 = match[0]
            for sep in ["/", "."]:
                if sep in value0:
                    parts = value0.split(sep)
                    return cls(*[int(v) for v in (parts[::-1] if len(parts[-1]) > 2 else parts)])

            return cls(*[int(v) for v in value0.split("-")])

        return cls(
            **{k: int(v.get("value")) if v and v.get("value") else None for k, v in value.items()}
        )

    def as_datetime(self):
        """Get 'datetime' data representation."""
        return datetime(self.year, self.month, self.day)

    def __str__(self):
        """Get string representation."""
        if self.year is None:
            return ""
        else:
            res = "%04d" % int(self.year)
            if self.month:
                res += "-%02d" % int(self.month)
            return res + "-%02d" % int(self.day) if self.day else res


PartialDate.__new__.__defaults__ = (None,) * len(PartialDate._fields)


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

    field_type = "varchar(10)"

    def db_value(self, value):
        """Convert into partial ISO date textual representation: YYYY-**-**, YYYY-MM-**, or YYYY-MM-DD."""
        if isinstance(value, str):
            value = PartialDate.create(value)

        if value is None or not value.year:
            return None

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
        return PartialDate(**dict(zip_longest(("year", "month", "day"), parts)))


class UUIDField(Field):
    """UUID field using build-in DBMS data type."""

    field_type = "uuid"

    def db_value(self, value):
        """Return DB representation."""
        return (
            value.hex
            if isinstance(value, uuid.UUID)
            else (value.replace("-", "") if "-" in value else value)
        )

    def python_value(self, value):
        """Return Python representation."""
        return uuid.UUID(value)


class TaskType(IntEnum):
    """Enum used to represent Task type."""

    NONE = 0
    AFFILIATION = 4  # Affilation of employment/education
    FUNDING = 1  # Funding
    WORK = 2
    PEER_REVIEW = 3
    OTHER_ID = 5
    PROPERTY = 8
    RESOURCE = 9
    SYNC = 11

    def __eq__(self, other):
        if isinstance(other, TaskType):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return self.name == other or self.name == getattr(other, "name", None)

    def __hash__(self):
        return hash(self.name)

    @classmethod
    def options(cls):
        """Get list of all types for UI dropown option list."""
        return [(e, e.name.replace("_", " ").title()) for e in cls]


class TaskTypeField(SmallIntegerField):
    """Partial date custom DB data field mapped to varchar(10)."""

    def db_value(self, value):
        """Change enum value to small int."""
        if value is None:
            return None
        try:
            if isinstance(value, TaskType):
                return value.value
            elif isinstance(value, int):
                return value
            elif isinstance(value, str):
                if str.isdigit(value):
                    return int(value)
                return TaskType[value.upper()].value
            else:
                raise ValueError("Unknow TaskType: '%s'", value)
        except:
            app.logger.exception("Failed to coerce the TaskType value, choosing NULL.")
            return None

    def python_value(self, value):
        """Parse partial ISO date textual representation."""
        if value is None:
            return None
        try:
            return TaskType(value)
        except:
            app.logger.exception(f"Failed to map DB value {value} to TaskType, choosing None.")
            return None


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
        return self.name == other or self.name == getattr(other, "name", None)

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
    DST = 4  # Distinction
    POS = 8  # Invited Position
    QUA = 16  # Qualification
    MEM = 32  # Membership
    SER = 64  # Service

    def __eq__(self, other):
        if isinstance(other, Affiliation):
            return self.value == other.value
        return self.name == other or self.name == getattr(other, "name", None)

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return ", ".join(
            {
                self.EDU: "Education",
                self.EMP: "Employment",
                self.DST: "Distinction",
                self.POS: "Invited-Position",
                self.QUA: "Qualification",
                self.MEM: "Membership",
                self.SER: "Service",
            }[a]
            for a in Affiliation
            if a & self
        )


class BaseModel(Model):
    """Encapsulate common bits and pieces of the model classes."""

    def field_is_updated(self, field_name):
        """Test if field is 'dirty'."""
        return any(field_name == f.name for f in self.dirty_fields)

    def save(self, *args, **kwargs):
        """Consistency validation and saving."""
        if self.is_dirty() and hasattr(self, "task") and self.task:
            self.task.updated_at = datetime.utcnow()
            self.task.save()
        if self.is_dirty() and getattr(self, "email", False) and self.field_is_updated("email"):
            self.email = self.email.lower()
        return super().save(*args, **kwargs)

    def add_status_line(self, line):
        """Add a text line to the status for logging processing progress."""
        ts = datetime.utcnow().isoformat(timespec="seconds")
        self.status = (self.status + "\n" if self.status else "") + ts + ": " + line

    @classmethod
    def get(cls, *query, **kwargs):
        """Get a single model instance."""
        if query and not kwargs and len(query) == 1 and isinstance(query[0], (int, str)):
            return super().get(id=query[0])
        elif not query and not kwargs:
            return cls.select().limit(1).first()
        return super().get(*query, **kwargs)

    @classmethod
    def last(cls):
        """Get last inserted entry."""
        return cls.select().order_by(cls.id.desc()).limit(1).first()

    @classmethod
    def model_class_name(cls):
        """Get the class name of the model."""
        return cls._meta.name

    @classmethod
    def underscore_name(cls):
        """Get the class underscore name of the model."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def __to_dashes(self, o):
        """Replace '_' with '-' in the dict keys."""
        if isinstance(o, dict):
            return {k.replace("_", "-"): self.__to_dashes(v) for k, v in o.items()}
        return o

    def to_dict(
        self,
        to_dashes=False,
        exclude_nulls=False,
        recurse=True,
        backrefs=False,
        only=None,
        exclude=None,
        seen=None,
        extra_attrs=None,
        fields_from_query=None,
        max_depth=None,
    ):
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
            max_depth=max_depth,
        )
        if exclude_nulls:
            o = {k: v for (k, v) in o.items() if v is not None}
        for k, v in o.items():
            if isinstance(v, PartialDate):
                o[k] = str(v)
            elif k == "task_type":
                o[k] = v.name
        if to_dashes:
            return self.__to_dashes(o)
        return o

    def has_field(self, field_name):
        """Check if the model has a field."""
        return field_name in self._meta.fields

    class Meta:  # noqa: D101,D106
        database = db
        only_save_dirty = True
        legacy_table_names = False


# class ModelDeferredRelation(DeferredRelation):
#     """Fixed DefferedRelation to allow inheritance and mixins."""

#     def set_model(self, rel_model):
#         """Include model in the generated "backref" to make it unique."""
#         for model, field, name in self.fields:
#             if isinstance(field, ForeignKeyField) and not field._backref:
#                 field._backref = "%s_%s_set" % (model.model_class_name(), name)

#         super().set_model(rel_model)


# User = ModelDeferredRelation()


class AuditedModel(BaseModel):
    """Mixing for getting data necessary for data change audit trail maintenance."""

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(null=True, default=None)
    is_deleted = BooleanField(null=True, default=False)

    # created_by = ForeignKeyField(User, on_delete="SET NULL", null=True, backref='+')
    # updated_by = ForeignKeyField(User, on_delete="SET NULL", null=True, backref='+')
    # created_by = IntegerField(null=True, index=True)
    # updated_by = IntegerField(null=True, index=True)
    created_by = DeferredForeignKey("User", on_delete="SET NULL", null=True, backref="+")
    updated_by = DeferredForeignKey("User", on_delete="SET NULL", null=True, backref="+")

    def save(self, *args, **kwargs):  # noqa: D102
        if self.is_dirty() and self._dirty != {"orcid_updated_at"}:
            self.updated_at = datetime.utcnow()
            if current_user and hasattr(current_user, "id"):
                if self.created_by:
                    self.updated_by_id = current_user.id
                elif hasattr(self, "created_by"):
                    self.created_by_id = current_user.id
        return super().save(*args, **kwargs)

    def delete_instance(self, *args, **kwargs):  # noqa: D102
        """Mark the entry id_deleted and save (with the link to the user that invoked the deletion) for audit trail."""
        self.is_deleted = True
        self.save()
        return super().delete_instance(*args, **kwargs)


class File(BaseModel):
    """Uploaded image files."""

    filename = CharField(max_length=100)
    data = BlobField()
    mimetype = CharField(max_length=30, column_name="mime_type")
    token = FixedCharField(max_length=8, unique=True, default=lambda: secrets.token_urlsafe(8)[:8])

    class Meta:  # noqa: D101,D106
        table_alias = "f"


class Organisation(AuditedModel):
    """Research organisation."""

    country_choices = [(c.alpha_2, c.name) for c in countries]
    country_choices.sort(key=lambda e: e[1])
    country_choices.insert(0, ("", "Country"))

    name = CharField(max_length=100, unique=True, null=True)
    saml_name = CharField(max_length=80, unique=True, null=True)
    if ENV != "prod":
        orcid_client_id = CharField(max_length=80, null=True)
        orcid_secret = CharField(max_length=80, null=True)
    else:  # pragma: no cover
        orcid_client_id = CharField(max_length=80, unique=True, null=True)
        orcid_secret = CharField(max_length=80, unique=True, null=True)
    confirmed = BooleanField(default=False)
    city = CharField(null=True)
    region = CharField(null=True, verbose_name="State/Region", max_length=100)
    country = CharField(null=True, choices=country_choices, default=DEFAULT_COUNTRY)
    disambiguated_id = CharField(null=True)
    disambiguation_source = CharField(null=True, choices=disambiguation_source_choices)
    is_email_sent = BooleanField(default=False)
    tech_contact = DeferredForeignKey(
        "User",
        backref="tech_contact_of",
        on_delete="SET NULL",
        null=True,
        help_text="Organisation technical contact",
    )
    # created_by = DeferredForeignKey("User", on_delete="SET NULL", null=True)
    # updated_by = DeferredForeignKey("User", on_delete="SET NULL", null=True)

    api_credentials_requested_at = DateTimeField(
        null=True,
        help_text="The time stamp when the user clicked on the button to register client API.",
    )
    api_credentials_entered_at = DateTimeField(
        null=True, help_text="The time stamp when the user entered API Client ID and secret."
    )

    can_use_api = BooleanField(null=True, help_text="The organisation can access ORCID Hub API.")
    logo = ForeignKeyField(
        File, on_delete="CASCADE", null=True, help_text="The logo of the organisation"
    )
    email_template = TextField(null=True)
    email_template_enabled = BooleanField(null=True, default=False)
    webhook_enabled = BooleanField(default=False, null=True)
    webhook_url = CharField(max_length=100, null=True)
    webhook_append_orcid = BooleanField(
        null=True,
        verbose_name="Append ORCID iD",
        help_text="Append the ORCID iD of the user the Webhook URL",
    )
    webhook_apikey = CharField(null=True, max_length=20)
    email_notifications_enabled = BooleanField(default=False, null=True)
    notification_email = CharField(
        max_length=100, null=True, verbose_name="Notification Email Address"
    )

    @property
    def invitation_sent_at(self):
        """Get the timestamp of the most recent invitation sent to the technical contact."""
        row = (
            self.org_invitations.select(fn.MAX(OrgInvitation.created_at).alias("last_sent_at"))
            .where(OrgInvitation.invitee_id == self.tech_contact_id)
            .first()
        )
        if row:
            return row.last_sent_at

    @property
    def invitation_confirmed_at(self):
        """Get the timestamp when the invitation link was opened."""
        row = (
            self.org_invitations.select(
                fn.MAX(OrgInvitation.created_at).alias("last_confirmed_at")
            )
            .where(OrgInvitation.invitee_id == self.tech_contact_id)
            .where(OrgInvitation.confirmed_at.is_null(False))
            .first()
        )
        if row:
            return row.last_confirmed_at

    @property
    def users(self):
        """Get organisation's user query."""
        return (
            User.select().join(UserOrg, on=(UserOrg.user_id == User.id)).where(UserOrg.org == self)
        )

    @property
    def admins(self):
        """Get organisation's administrator query."""
        return self.users.where(UserOrg.is_admin)

    def __str__(self):
        return self.name or self.saml_name

    def save(self, *args, **kwargs):
        """Handle data consistency validation and saving."""
        if self.is_dirty():

            if self.name is None:
                self.name = self.saml_name

            if self.field_is_updated("tech_contact") and self.tech_contact:
                if not self.tech_contact.has_role(Role.TECHNICAL):
                    self.tech_contact.roles |= Role.TECHNICAL
                    self.tech_contact.save()
                    app.logger.info(f"Added TECHNICAL role to user {self.tech_contact}")

            super().save(*args, **kwargs)

    class Meta:  # noqa: D101,D106
        table_alias = "o"


class User(AuditedModel, UserMixin):
    """
    ORCiD Hub user.

    It's a generic user including researchers, organisation administrators, hub administrators, etc.
    """

    name = CharField(max_length=64, null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    email = CharField(max_length=120, unique=True, null=True, verbose_name="Email Address")
    eppn = CharField(max_length=120, unique=True, null=True, verbose_name="EPPN")
    orcid = OrcidIdField(null=True, help_text="User's ORCID iD")
    confirmed = BooleanField(default=False)
    # Role bit-map:
    roles = SmallIntegerField(default=0)

    is_locked = BooleanField(default=False)
    webhook_enabled = BooleanField(default=False, null=True)
    orcid_updated_at = DateTimeField(null=True, default=None)

    # TODO: many-to-many
    # NB! Deprecated!
    # TODO: we still need to remember the organisation that last authenticated the user
    organisation = ForeignKeyField(
        Organisation, backref="members", on_delete="SET NULL", null=True
    )
    created_by = ForeignKeyField("self", on_delete="SET NULL", null=True, backref="+")
    updated_by = ForeignKeyField("self", on_delete="SET NULL", null=True, backref="+")

    def __str__(self):
        if self.name and (self.eppn or self.email):
            return f"{self.name} ({self.email or self.eppn})"
        return self.name or self.email or self.orcid or super().__str__()

    @property
    def full_name(self):
        """Full name of the user."""
        value = self.first_name or ""
        if value:
            value += " "
        value += self.last_name or ""
        if not value:
            value = self.name or ""
        return value

    @property
    def full_name_with_email(self):
        """Full name with the email address of the user."""
        value = self.full_name
        if value:
            value += " "
        return f"{value}({self.email or self.eppn})"

    @property
    def username(self):
        """Usename for comlying with Flask-Login API."""
        return self.orcid or self.email

    @property
    def organisations(self):
        """Get all linked to the user organisation query."""
        return (
            Organisation.select(
                Organisation,
                (Organisation.tech_contact_id == self.id).alias("is_tech_contact"),
                ((UserOrg.is_admin.is_null(False)) & (UserOrg.is_admin)).alias("is_admin"),
                (fn.COALESCE(UserOrg.email, self.email).alias("current_email")),
            )
            .join(UserOrg, on=(UserOrg.org_id == Organisation.id))
            .where(UserOrg.user_id == self.id)
        )

    @lazy_property
    @cache.memoize(50)
    def org_links(self):
        """Get all user organisation linked directly and indirectly."""
        if self.orcid:
            q = (
                UserOrg.select()
                .join(
                    User,
                    on=(
                        (User.id == UserOrg.user_id)
                        & ((User.email == self.email) | (User.orcid == self.orcid))
                    ),
                )
                .where(
                    (UserOrg.user_id == self.id)
                    | (User.email == self.email)
                    | (User.orcid == self.orcid)
                )
            )
        else:
            q = self.userorg_set

        return [
            r
            for r in q.select(
                UserOrg,
                Organisation.name.alias("org_name"),
                (Organisation.id == self.organisation_id).alias("current_org"),
            )
            .join(Organisation, on=(Organisation.id == UserOrg.org_id))
            .order_by(Organisation.name)
            .objects()
        ]

    @property
    def available_organisations(self):
        """Get all not yet linked to the user organisation query."""
        return (
            Organisation.select(Organisation)
            .where(UserOrg.id.is_null())
            .join(
                UserOrg,
                JOIN.LEFT_OUTER,
                on=((UserOrg.org_id == Organisation.id) & (UserOrg.user_id == self.id)),
            )
        )

    @property
    def admin_for(self):
        """Get organisations the user is admin for (query)."""
        return self.organisations.where(UserOrg.is_admin)

    @property
    def is_active(self):
        """Get 'is_active' based on confirmed for Flask-Login.

        TODO: confirmed - user that email is confirmed either by IdP or by confirmation email
        isn't the same as "is active".
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
        elif isinstance(role, int):
            return bool(role & self.roles)
        else:
            return False

    @property
    def is_superuser(self):
        """Test if the user is a HUB admin."""
        return bool(self.roles & Role.SUPERUSER)

    @is_superuser.setter
    def is_superuser(self, value):  # noqa: D401
        """Set user as a HUB admin."""
        if value:
            self.roles |= Role.SUPERUSER.value
        else:
            self.roles &= ~Role.SUPERUSER.value

    @property
    def is_admin(self):
        """Test if the user belongs to the organisation admin."""
        return bool(self.roles & Role.ADMIN)

    def avatar(self, size=40, default="identicon"):
        """Return Gravatar service user avatar URL."""
        # TODO: default gravatar image
        # default = "https://www.example.com/default.jpg"
        gravatar_url = (
            "https://www.gravatar.com/avatar/" + md5(self.email.lower().encode()).hexdigest() + "?"
        )
        gravatar_url += urlencode({"d": default, "s": str(size)})
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
        """Indicate if the user is the technical contact of the organisation."""
        if org is None:
            org = self.organisation
        return org and org.tech_contact and org.tech_contact_id == self.id

    def is_admin_of(self, org=None):
        """Indicate if the user is the technical contact of the organisation."""
        if org is None:
            org = self.organisation
        return (
            org
            and UserOrg.select()
            .where(UserOrg.user == self, UserOrg.org == org, UserOrg.is_admin)
            .exists()
        )

    @property
    def uuid(self):
        """Generate UUID for the user based on the primary email."""
        return uuid.uuid5(uuid.NAMESPACE_URL, "mailto:" + (self.email or self.eppn))

    class Meta:  # noqa: D101,D106
        table_alias = "u"


class OrgInfo(BaseModel):
    """Preloaded organisation data."""

    name = CharField(max_length=100, unique=True, help_text="Organisation name")
    saml_name = CharField(max_length=100, unique=True, null=True, help_text="SAML Name")
    title = CharField(null=True, help_text="Contact Person Tile")
    first_name = CharField(null=True, help_text="Contact Person's First Name")
    last_name = CharField(null=True, help_text="Contact Person's Last Name")
    role = CharField(null=True, help_text="Contact Person's Role")
    email = CharField(null=True, help_text="Contact Person's Email Address")
    phone = CharField(null=True, help_text="Contact Person's Phone")
    is_public = BooleanField(
        null=True, default=False, help_text="Permission to post contact information to WEB"
    )
    country = CharField(null=True, help_text="Country Code", default=DEFAULT_COUNTRY)
    city = CharField(null=True, help_text="City of Home Campus")
    disambiguated_id = CharField(
        null=True, verbose_name="Identifier", help_text="Organisation disambiguated identifier"
    )
    disambiguation_source = CharField(
        null=True,
        verbose_name="Source",
        help_text="Organisation disambiguated ID source",
        choices=disambiguation_source_choices,
    )

    def __str__(self):
        return self.name or self.disambiguated_id or super().__str__()

    class Meta:  # noqa: D101,D106
        table_alias = "oi"

    @classmethod
    def load_from_csv(cls, source):
        """Load data from CSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source, newline="")
        reader = csv.reader(source)
        header = next(reader)

        assert len(header) >= 3, (
            "Wrong number of fields. Expected at least 3 fields "
            "(name, disambiguated organisation ID, and disambiguation source). "
            "Read header: %s" % header
        )
        header_rexs = [
            re.compile(ex, re.I)
            for ex in (
                "organisation|name",
                "title",
                r"first\s*(name)?",
                r"last\s*(name)?",
                "role",
                "email",
                "phone",
                "public|permission to post to web",
                r"country\s*(code)?",
                "city",
                "(common:)?disambiguated.*identifier",
                "(common:)?disambiguation.*source",
                r"saml|tuakiri\s*(name)?",
            )
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
                return None if v == "" else v

        for row in reader:
            # skip empty lines:
            if not row or row is None or len(row) == 0 or (len(row) == 1 and row[0].strip() == ""):
                continue

            name = val(row, 0)
            oi, _ = cls.get_or_create(name=name)

            oi.title = val(row, 1)
            oi.first_name = val(row, 2)
            oi.last_name = val(row, 3)
            oi.role = val(row, 4)
            oi.email = normalize_email(val(row, 5))
            oi.phone = val(row, 6)
            oi.is_public = val(row, 7) and val(row, 7).upper() == "YES"
            oi.country = val(row, 8) or DEFAULT_COUNTRY
            oi.city = val(row, 9)
            oi.disambiguated_id = val(row, 10)
            oi.disambiguation_source = val(row, 11)
            oi.saml_name = val(row, 12)

            oi.save()

        return reader.line_num - 1


class OrgInvitation(AuditedModel):
    """Organisation invitation to on-board the Hub."""

    invitee = ForeignKeyField(
        User, on_delete="CASCADE", null=True, backref="received_org_invitations"
    )
    inviter = ForeignKeyField(
        User, on_delete="SET NULL", null=True, backref="sent_org_invitations"
    )
    org = ForeignKeyField(Organisation, on_delete="SET NULL", verbose_name="Organisation")
    email = TextField(
        help_text="The email address the invitation was sent to.",
        verbose_name="Invitee Email Address",
    )
    token = TextField(unique=True)
    confirmed_at = DateTimeField(null=True)
    tech_contact = BooleanField(
        null=True,
        help_text="The invitee is the technical contact of the organisation.",
        verbose_name="Is Tech.contact",
    )
    url = CharField(null=True)

    @property
    def sent_at(self):
        """Get the time the invitation was sent."""
        return self.created_at

    class Meta:  # noqa: D101,D106
        table_alias = "oi"


class UserOrg(AuditedModel):
    """Linking object for many-to-many relationship."""

    user = ForeignKeyField(User, on_delete="CASCADE", index=True, backref="user_orgs")
    org = ForeignKeyField(
        Organisation,
        on_delete="CASCADE",
        index=True,
        verbose_name="Organisation",
        backref="user_orgs",
    )
    is_admin = BooleanField(
        null=True, default=False, help_text="User is an administrator for the organisation"
    )
    # ALTER TABLE user_org ADD COLUMN "email" VARCHAR(120) NULL;
    # ALTER TABLE audit.user_org ADD COLUMN "email" VARCHAR(120) NULL;
    email = CharField(max_length=120, unique=True, null=True, verbose_name="User Organisation Email Address")

    # Affiliation bit-map:
    affiliations = SmallIntegerField(default=0, null=True, verbose_name="EDU Person Affiliations")

    # TODO: the access token should be either here or in a separate list
    # access_token = CharField(max_length=120, unique=True, null=True)

    @property
    def current_email(self):
        """User organisation email address"""
        return self.email or (self.user and self.user.email)

    def save(self, *args, **kwargs):
        """Enforce foreign key constraints and consolidate user roles with the linked organisations.

        Enforce foreign key constraints and consolidate user roles with the linked organisations
        before saving data.
        """
        if self.is_dirty():
            # if self.field_is_updated("org"):
            #     self.org  # just enforce re-querying
            user = self.user
            if self.is_admin != user.is_admin:
                if (
                    self.is_admin
                    or UserOrg.select()
                    .where(
                        (UserOrg.user_id == self.user_id)
                        & (UserOrg.org_id != self.org_id)
                        & UserOrg.is_admin
                    )
                    .exists()
                ):  # noqa: E125
                    user.roles |= Role.ADMIN
                    app.logger.info(f"Added ADMIN role to user {user}")
                else:
                    user.roles &= ~Role.ADMIN
                    app.logger.info(f"Revoked ADMIN role from user {user}")
                user.save()

            return super().save(*args, **kwargs)

    class Meta:  # noqa: D101,D106
        table_alias = "uo"
        indexes = ((("user", "org"), True),)


class OrcidToken(AuditedModel):
    """For Keeping ORCID token in the table."""

    user = ForeignKeyField(
        User, null=True, index=True, backref="orcid_tokens", on_delete="CASCADE"
    )  # TODO: add validation for 3-legged authorization tokens
    org = ForeignKeyField(
        Organisation, index=True, verbose_name="Organisation", backref="orcid_tokens"
    )
    scopes = TextField(null=True)
    access_token = CharField(max_length=36, unique=True, null=True)
    issue_time = DateTimeField(default=datetime.utcnow)
    refresh_token = CharField(max_length=36, unique=True, null=True)
    expires_in = IntegerField(default=0)
    # created_by = ForeignKeyField(User, on_delete="SET NULL", null=True, backref='+')
    # updated_by = ForeignKeyField(User, on_delete="SET NULL", null=True, backref='+')

    class Meta:  # noqa: D101,D106
        table_alias = "ot"


class UserOrgAffiliation(AuditedModel):
    """For Keeping the information about the affiliation."""

    user = ForeignKeyField(User, on_delete="CASCADE", backref="org_affiliations")
    organisation = ForeignKeyField(
        Organisation, index=True, on_delete="CASCADE", verbose_name="Organisation"
    )
    disambiguated_id = CharField(verbose_name="Disambiguation ORG Id", null=True)
    disambiguation_source = CharField(
        verbose_name="Disambiguation ORG Source", null=True, choices=disambiguation_source_choices
    )
    name = TextField(null=True, verbose_name="Institution/employer")
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    department_name = TextField(null=True)
    department_city = TextField(null=True)
    role_title = TextField(null=True)
    put_code = IntegerField(null=True)
    path = TextField(null=True)
    # created_by = ForeignKeyField(User, on_delete="SET NULL", null=True, backref='+')
    # updated_by = ForeignKeyField(User, on_delete="SET NULL", null=True, backref='+')

    class Meta:  # noqa: D101,D106
        table_name = "user_organisation_affiliation"
        table_alias = "oua"


class OrcidApiCall(BaseModel):
    """ORCID API call audit entry."""

    called_at = DateTimeField(default=datetime.utcnow)
    user = ForeignKeyField(User, null=True, on_delete="SET NULL", backref="orcid_api_calls")
    method = CharField(max_length=6)
    url = CharField()
    query_params = TextField(null=True)
    body = TextField(null=True)
    put_code = IntegerField(null=True)
    response = TextField(null=True)
    response_time_ms = IntegerField(null=True)
    status = IntegerField(null=True)

    def set_response_time(self):
        """Calculate and set the response time assuming the call finished right now."""
        self.response_time_ms = round((datetime.utcnow() - self.called_at).microseconds / 1000)

    class Meta:  # noqa: D101,D106
        table_alias = "oac"


class OrcidAuthorizeCall(BaseModel):
    """ORCID Authorize call audit entry."""

    called_at = DateTimeField(default=datetime.utcnow)
    user = ForeignKeyField(
        User, null=True, default=None, on_delete="SET NULL", backref="orcid_auth_calls"
    )
    method = TextField(null=True, default="GET")
    url = TextField(null=True)
    token = TextField(null=True)
    state = TextField(null=True)
    response_time_ms = IntegerField(null=True)

    class Meta:  # noqa: D101,D106
        table_alias = "oac"


class Task(AuditedModel):
    """Batch processing task created form CSV/TSV file."""

    org = ForeignKeyField(
        Organisation, index=True, verbose_name="Organisation", on_delete="CASCADE", backref="tasks"
    )
    completed_at = DateTimeField(null=True)
    filename = TextField(null=True)
    is_raw = BooleanField(null=True, default=False)
    task_type = TaskTypeField(
        default=TaskType.NONE, choices=[(tt.value, tt.name) for tt in TaskType if tt.value]
    )
    expires_at = DateTimeField(null=True)
    expiry_email_sent_at = DateTimeField(null=True)
    status = CharField(null=True, max_length=10, choices=[(v, v) for v in ["ACTIVE", "RESET"]])

    def __str__(self):
        return (
            "Synchronization task"
            if self.task_type == TaskType.SYNC
            else (
                self.filename
                or f"{TaskType(self.task_type).name.capitalize()} record processing task #{self.id}"
            )
        )

    @property
    def is_expiry_email_sent(self):
        """Test if the expiry email is sent ot not."""
        return bool(self.expiry_email_sent_at)

    @lazy_property
    def record_count(self):
        """Get count of the loaded recoreds."""
        return 0 if self.records is None or not self.task_type else self.records.count()

    @property
    def record_model(self):
        """Get record model class."""
        return self.records.model

    @lazy_property
    def records(self):
        """Get all task record query."""
        if not self.task_type or self.task_type in [TaskType.SYNC, TaskType.NONE]:
            return None
        if self.is_raw:
            return MessageRecord.select().where(MessageRecord.task == self)
        return getattr(self, self.task_type.name.lower() + "_records")

    @lazy_property
    def completed_count(self):
        """Get number of completed rows."""
        return self.records.where(self.record_model.processed_at.is_null(False)).count()

    @lazy_property
    def completed_percent(self):
        """Get the percentage of completed rows."""
        return (100.0 * self.completed_count) / self.record_count if self.record_count else 0.0

    @property
    def error_count(self):
        """Get error count encountered during processing batch task."""
        return self.records.where(self.record_model.status ** "%error%").count()

    @property
    def is_ready(self):
        """Indicate that the task is 'ready to go'.

        The task is 'ready to go' if:
            - the task is "ACTIVE"
            or
            - there is at least one activated record.
        """
        return self.state == "ACTIVE" or self.records.whhere(self.record_model.is_active).exists()

    def to_dict(self, to_dashes=True, recurse=None, exclude=None, include_records=None, only=None):
        """Create a dict represenatation of the task suitable for serialization into JSON or YAML."""
        # TODO: expand for the other types of the tasks
        task_dict = super().to_dict(
            recurse=False,
            to_dashes=to_dashes,
            exclude=exclude,
            only=only
            or [
                Task.id,
                Task.filename,
                Task.task_type,
                Task.created_at,
                Task.updated_at,
                Task.status,
                Task.is_raw,
            ],
        )
        # TODO: refactor for funding task to get records here not in API or export
        if (recurse or include_records or recurse is None) and self.task_type not in [
            TaskType.FUNDING,
            TaskType.SYNC,
        ]:
            if self.task_type == TaskType.AFFILIATION:
                task_dict["records"] = [
                    r.to_dict(
                        external_id=[
                            ae.to_export_dict()
                            for ae in AffiliationExternalId.select().where(
                                AffiliationExternalId.record_id == r.id
                            )
                        ],
                        to_dashes=to_dashes,
                        recurse=recurse,
                        exclude=[self.record_model.task],
                    )
                    for r in self.records
                ]
            else:
                task_dict["records"] = [
                    r.to_dict(
                        to_dashes=to_dashes, recurse=recurse, exclude=[self.record_model.task]
                    )
                    for r in self.records
                ]
        return task_dict

    def to_export_dict(self, include_records=True):
        """Create a dictionary representation for export."""
        if self.task_type == TaskType.AFFILIATION:
            task_dict = self.to_dict(recurse=include_records, include_records=include_records)
        else:
            task_dict = self.to_dict(
                recurse=False,
                to_dashes=True,
                include_records=False,
                exclude=[Task.created_by, Task.updated_by, Task.org, Task.task_type],
            )
            task_dict["task-type"] = self.task_type.name
            if include_records:
                task_dict["records"] = [r.to_export_dict() for r in self.records]
        return task_dict

    class Meta:  # noqa: D101,D106
        table_alias = "t"


class Log(BaseModel):
    """Task log entries."""

    created_at = DateTimeField(default=datetime.utcnow)
    created_by = ForeignKeyField(User, on_delete="SET NULL", null=True, backref="+")
    task = ForeignKeyField(
        Task,
        on_delete="CASCADE",
        null=True,
        index=True,
        verbose_name="Task",
        backref="log_entries",
    )
    message = TextField(null=True)

    class Meta:  # noqa: D101,D106
        table_alias = "l"

    def save(self, *args, **kwargs):  # noqa: D102
        if self.is_dirty():
            if current_user and hasattr(current_user, "id"):
                if hasattr(self, "created_by"):
                    self.created_by_id = current_user.id
        return super().save(*args, **kwargs)


class UserInvitation(AuditedModel):
    """Organisation invitation to on-board the Hub."""

    invitee = ForeignKeyField(
        User, on_delete="CASCADE", null=True, backref="received_user_invitations"
    )
    inviter = ForeignKeyField(
        User, on_delete="SET NULL", null=True, backref="sent_user_invitations"
    )
    org = ForeignKeyField(
        Organisation,
        on_delete="CASCADE",
        null=True,
        verbose_name="Organisation",
        backref="user_invitations",
    )
    task = ForeignKeyField(
        Task,
        on_delete="CASCADE",
        null=True,
        index=True,
        verbose_name="Task",
        backref="user_invitations",
    )
    email = CharField(
        index=True,
        null=True,
        max_length=80,
        help_text="The email address the invitation was sent to.",
    )
    first_name = TextField(null=True)
    last_name = TextField(null=True)
    orcid = OrcidIdField(null=True)
    department = TextField(verbose_name="Campus/Department", null=True)
    organisation = TextField(verbose_name="Organisation Name", null=True)
    city = TextField(null=True)
    region = TextField(verbose_name="State/Region", null=True)
    country = CharField(verbose_name="Country", max_length=2, null=True)
    course_or_role = TextField(verbose_name="Course or Job title", null=True)
    start_date = PartialDateField(verbose_name="Start date", null=True)
    end_date = PartialDateField(verbose_name="End date (leave blank if current)", null=True)
    affiliations = SmallIntegerField(
        verbose_name="User affiliations", null=True, default=Affiliation.NONE
    )
    disambiguated_id = TextField(verbose_name="Disambiguation ORG Id", null=True)
    disambiguation_source = TextField(
        verbose_name="Disambiguation ORG Source", null=True, choices=disambiguation_source_choices
    )
    token = TextField(unique=True)
    confirmed_at = DateTimeField(null=True)
    is_person_update_invite = BooleanField(
        default=False,
        verbose_name="'Person/Update' Invitation",
        help_text="Invitation to grant 'Person/Update' scope",
    )

    @property
    def sent_at(self):
        """Get the time the invitation was sent."""
        return self.created_at

    class Meta:  # noqa: D101,D106
        table_alias = "ui"


class RecordModel(BaseModel):
    """Common model bits of the task records."""

    def key_name(self, name):
        """Map key-name to a model class key name for export."""
        return name

    @classmethod
    def get_field_regxes(cls):
        """Return map of compiled field name regex to the model fields."""
        return {f: re.compile(e, re.I) for (f, e) in cls._field_regex_map}

    @property
    def invitee_model(self):
        """Get invitee model class."""
        if hasattr(self, "invitees"):
            return self.invitees.model

    def to_export_dict(self):
        """Map the common record parts to dict for export into JSON/YAML."""
        org = self.task.org
        d = {"type": self.type} if self.has_field("type") else {}
        if hasattr(self, "org_name"):
            d["organization"] = {
                "disambiguated-organization": {
                    "disambiguated-organization-identifier": self.disambiguated_id
                    or org.disambiguated_id,
                    "disambiguation-source": self.disambiguation_source
                    or org.disambiguation_source,
                },
                "name": self.org_name or org.name,
                "address": {
                    "city": self.city or org.city,
                    "region": self.region or org.region,
                    "country": self.country or org.country,
                },
            }
        if self.has_field("title"):
            d["title"] = {
                "title": {"value": self.title},
                "translated-title": {
                    "value": self.translated_title,
                    "language-code": self.translated_title_language_code,
                },
            }
        if hasattr(self, "invitees") and self.invitees:
            d["invitees"] = [r.to_export_dict() for r in self.invitees]
        if hasattr(self, "contributors") and self.contributors:
            d["contributors"] = {"contributor": [r.to_export_dict() for r in self.contributors]}
        if hasattr(self, "external_ids") and self.external_ids:
            d[self.key_name("external-ids")] = {
                "external-id": [r.to_export_dict() for r in self.external_ids]
            }
        if hasattr(self, "start_date") and self.start_date:
            d["start-date"] = self.start_date.as_orcid_dict()
        if hasattr(self, "end_date") and self.end_date:
            d["end-date"] = self.end_date.as_orcid_dict()
        return d

    def orcid_external_id(self, type=None, value=None, url=None, relationship=None):
        """Get the object rendering into an ORCID API 3.x external-id."""
        if (not type and not value) and (not self.external_id_type or not self.external_id_value):
            return

        ei = {
            "external-id-type": type or self.external_id_type,
            "external-id-value": value or self.external_id_value,
        }

        if self.external_id_relationship:
            ei["external-id-relationship"] = relationship or self.external_id_relationship

        if self.external_id_url:
            ei["external-id-url"] = {"value": url or self.external_id_url}

        return ei


class GroupIdRecord(RecordModel):
    """GroupID records."""

    type_choices = [
        ("publisher", "publisher"),
        ("institution", "institution"),
        ("journal", "journal"),
        ("conference", "conference"),
        ("newspaper", "newspaper"),
        ("newsletter", "newsletter"),
        ("magazine", "magazine"),
        ("peer-review service", "peer-review service"),
    ]
    type_choices.sort(key=lambda e: e[1])
    type_choices.insert(0, ("", ""))
    put_code = IntegerField(null=True)
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")
    name = CharField(
        max_length=120,
        help_text="The name of the group. This can be the name of a journal (Journal of Criminal Justice),"
        " a publisher (Society of Criminal Justice), or non-specific description (Legal Journal)"
        " as required.",
    )
    group_id = CharField(
        max_length=120,
        help_text="The group's identifier, formatted as type:identifier, e.g. ringgold:12345678. "
        "This can be as specific (e.g. the journal's ISSN) or vague as required. "
        "Valid types include: ringgold:|issn:|orcid-generated:|fundref:|publons:",
    )
    description = CharField(
        max_length=1000,
        help_text="A brief textual description of the group. "
        "This can be as specific or vague as required.",
    )
    type = CharField(
        max_length=80,
        choices=type_choices,
        help_text="One of the specified types: publisher; institution; journal; conference; newspaper; "
        "newsletter; magazine; peer-review service.",
    )
    organisation = ForeignKeyField(
        Organisation, backref="group_id_records", on_delete="CASCADE", null=True
    )

    class Meta:  # noqa: D101,D106
        table_alias = "gid"


class AffiliationRecord(RecordModel):
    """Affiliation record loaded from CSV file for batch processing."""

    is_active = BooleanField(
        default=False, help_text="The record is marked 'active' for batch processing", null=True
    )
    task = ForeignKeyField(Task, backref="affiliation_records", on_delete="CASCADE")
    put_code = IntegerField(null=True)
    local_id = CharField(
        max_length=100,
        null=True,
        verbose_name="Local ID",
        help_text="Record identifier used in the data source system.",
    )
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")
    first_name = CharField(null=True, max_length=120)
    last_name = CharField(null=True, max_length=120)
    email = CharField(max_length=80, null=True)
    orcid = OrcidIdField(null=True)
    organisation = CharField(null=True, index=True, max_length=200)
    affiliation_type = CharField(
        null=True,
        max_length=20,
        choices=[(v, v.replace("-", " ").title()) for v in AFFILIATION_TYPES],
    )
    role = CharField(null=True, verbose_name="Role/Course", max_length=100)
    department = CharField(null=True, max_length=200)
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    city = CharField(null=True, max_length=200)
    region = CharField(null=True, verbose_name="State/Region", max_length=100)
    country = CharField(null=True, max_length=2, choices=country_choices)
    disambiguated_id = CharField(null=True, verbose_name="Disambiguated Organization Identifier")
    disambiguation_source = CharField(
        null=True, max_length=100, choices=disambiguation_source_choices
    )
    delete_record = BooleanField(null=True)
    visibility = CharField(null=True, max_length=100, choices=visibility_choices)
    url = CharField(max_length=200, null=True)
    display_index = CharField(max_length=100, null=True)

    class Meta:  # noqa: D101,D106
        table_alias = "ar"

    _regex_field_map = [
        ("first_name", r"first\s*(name)?"),
        ("last_name", r"last\s*(name)?"),
        ("email", "email"),
        ("organisation", "organisation|^name"),
        ("department", "campus|department"),
        ("city", "city"),
        ("region", "state|region"),
        ("role", "course|title|role"),
        ("start_date", r"start\s*(date)?"),
        ("end_date", r"end\s*(date)?"),
        ("affiliation_type", r"affiliation(s)?\s*(type)?|student|staff"),
        ("country", "country"),
        ("disambiguated_id", r"disambiguat.*id"),
        ("disambiguation_source", r"disambiguat.*source"),
        ("put_code", r"put|code"),
        ("orcid", "orcid.*"),
        ("local_id", "local.*|.*identifier"),
    ]

    def to_dict(self, external_id=[], *args, **kwargs):
        """Create a dict and add external ids in affiliation records."""
        rd = super().to_dict(*args, **kwargs)
        if external_id:
            rd["external-id"] = external_id
        return rd

    @classmethod
    def load(
        cls,
        data,
        task=None,
        task_id=None,
        filename=None,
        override=True,
        skip_schema_validation=False,
        org=None,
    ):
        """Load afffiliation record task form JSON/YAML. Data shoud be already deserialize."""
        if isinstance(data, str):
            data = json.loads(data) if filename.lower().endswith(".json") else yaml.load(data)
        if org is None:
            org = current_user.organisation if current_user else None
        if not skip_schema_validation:
            jsonschema.validate(data, schemas.affiliation_task)
        if not task and task_id:
            task = Task.select().where(Task.id == task_id).first()
        if not task and "id" in data:
            task_id = int(data["id"])
            task = Task.select().where(Task.id == task_id).first()
        with db.atomic() as transaction:
            try:
                if not task:
                    filename = (
                        filename
                        or data.get("filename")
                        or datetime.utcnow().isoformat(timespec="seconds")
                    )
                    task = Task.create(org=org, filename=filename, task_type=TaskType.AFFILIATION)
                elif override:
                    AffiliationRecord.delete().where(AffiliationRecord.task == task).execute()
                record_fields = AffiliationRecord._meta.fields.keys()
                is_enqueue = False
                for r in data.get("records"):
                    if "id" in r and not override:
                        rec = AffiliationRecord.get(int(r["id"]))
                    else:
                        rec = AffiliationRecord(task=task)
                    for k, v in r.items():
                        if k == "id" or k.startswith(("external", "status", "processed")):
                            continue
                        k = k.replace("-", "_")
                        if k == "is_active" and v:
                            is_enqueue = v
                        if k in ["disambiguation_source"] and v:
                            v = v.upper()
                        if k in ["visibility", "affiliation_type"] and v:
                            v = v.replace("_", "-").lower()
                        if k in record_fields and rec.__data__.get(k) != v:
                            rec.__data__[k] = PartialDate.create(v) if k.endswith("date") else v
                            rec._dirty.add(k)
                    if rec.is_dirty():
                        validator = ModelValidator(rec)
                        if not validator.validate():
                            raise ModelExceptionError(f"Invalid record: {validator.errors}")
                        rec.save()
                        if r.get("external-id"):
                            for exi in r.get("external-id"):
                                ext_data = {
                                    k.replace("-", "_").replace("external_id_", ""): v.lower()
                                    if v
                                    else None
                                    for k, v in exi.items()
                                }
                                if ext_data.get("type") and ext_data.get("value"):
                                    ext_id = AffiliationExternalId.create(record=rec, **ext_data)
                                    if not ModelValidator(ext_id).validate():
                                        raise ModelExceptionError(
                                            f"Invalid affiliation exteral-id: {validator.errors}"
                                        )
                                    ext_id.save()
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
            except:
                transaction.rollback()
                app.logger.exception("Failed to load affiliation record task file.")
                raise
        return task

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load affiliation record data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source, newline="")
        reader = csv.reader(source)
        header = next(reader)
        if filename is None:
            if hasattr(source, "name"):
                filename = source.name
            else:
                filename = datetime.utcnow().isoformat(timespec="seconds")

        if len(header) == 1 and "\t" in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)
        if len(header) < 2:
            raise ModelExceptionError("Expected CSV or TSV format file.")

        if len(header) < 3:
            raise ModelExceptionError(
                "Wrong number of fields. Expected at least 4 fields "
                "(first name, last name, email address or another unique identifier, student/staff). "
                f"Read header: {header}"
            )

        header_rexs = [
            re.compile(ex, re.I)
            for ex in [
                r"first\s*(name)?",
                r"last\s*(name)?",
                "email",
                "organisation|^name",
                "campus|department",
                "city",
                "state|region",
                "course|title|role",
                r"start\s*(date)?",
                r"end\s*(date)?",
                r"affiliation(s)?\s*(type)?|student|staff",
                "country",
                r"disambiguat.*id",
                r"disambiguat.*source",
                r"put|code",
                "orcid.*",
                "local.*|.*identifier",
                "delete(.*record)?",
                r"(is)?\s*visib(bility|le)?",
                r"url",
                r"(display)?.*index",
                r"(external)?\s*id(entifier)?\s+type$",
                r"(external)?\s*id(entifier)?\s*(value)?$",
                r"(external)?\s*id(entifier)?\s*url",
                r"(external)?\s*id(entifier)?\s*rel(ationship)?",
                r"(is)?\s*active$",
            ]
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if column and rex.match(column.strip()):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        if all(idx is None for idx in idxs):
            raise ModelExceptionError(
                f"Failed to map fields based on the header of the file: {header}"
            )

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, i, default=None):
            if idxs[i] is None or idxs[i] >= len(row):
                return default
            else:
                v = row[idxs[i]].strip()
                return default if v == "" else v

        with db.atomic() as transaction:
            try:
                task = Task.create(org=org, filename=filename, task_type=TaskType.AFFILIATION)
                is_enqueue = False
                for row_no, row in enumerate(reader):
                    # skip empty lines:
                    if len([item for item in row if item and item.strip()]) == 0:
                        continue
                    if len(row) == 1 and row[0].strip() == "":
                        continue

                    put_code = val(row, 14)
                    delete_record = val(row, 17)
                    delete_record = delete_record and delete_record.lower() in [
                        "y",
                        "yes",
                        "ok",
                        "delete",
                        "1",
                    ]
                    if delete_record:
                        if not put_code:
                            raise ModelExceptionError(
                                f"Missing put-code. Cannot delete a record without put-code. "
                                f"#{row_no+2}: {row}. Header: {header}"
                            )

                    email = normalize_email(val(row, 2, ""))
                    orcid = validate_orcid_id(val(row, 15))
                    local_id = val(row, 16)

                    if not email and not orcid and local_id and validators.email(local_id):
                        # if email is missing and local ID is given as a valid email, use it:
                        email = local_id

                    # The uploaded country must be from ISO 3166-1 alpha-2
                    country = val(row, 11)
                    if country:
                        try:
                            country = countries.lookup(country).alpha_2
                        except Exception:
                            raise ModelExceptionError(
                                f" (Country must be 2 character from ISO 3166-1 alpha-2) in the row "
                                f"#{row_no+2}: {row}. Header: {header}"
                            )

                    if not delete_record and not (email or orcid):
                        raise ModelExceptionError(
                            f"Missing user identifier (email address or ORCID iD) in the row "
                            f"#{row_no+2}: {row}. Header: {header}"
                        )

                    if email and not validators.email(email):
                        raise ValueError(
                            f"Invalid email address '{email}'  in the row #{row_no+2}: {row}"
                        )

                    affiliation_type = val(row, 10)
                    if affiliation_type:
                        affiliation_type = affiliation_type.replace("_", "-").lower()
                    if not delete_record and (
                        not affiliation_type or affiliation_type.lower() not in AFFILIATION_TYPES
                    ):
                        raise ValueError(
                            f"Invalid affiliation type '{affiliation_type}' in the row #{row_no+2}: {row}. "
                            f"Expected values: {', '.join(at for at in AFFILIATION_TYPES)}."
                        )

                    first_name = val(row, 0)
                    last_name = val(row, 1)
                    if not delete_record and not (email or orcid):
                        raise ModelExceptionError(
                            "Wrong number of fields. Expected at least 4 fields "
                            "(first name, last name, email address or another unique identifier, "
                            f"student/staff): {row}"
                        )
                    disambiguation_source = val(row, 13)
                    if disambiguation_source:
                        disambiguation_source = disambiguation_source.upper()
                    visibility = val(row, 18)
                    if visibility:
                        visibility = visibility.replace("_", "-").lower()

                    is_active = val(row, 25, "").lower() in ["y", "yes", "1", "true"]
                    if is_active:
                        is_enqueue = is_active

                    af = cls(
                        task=task,
                        first_name=first_name,
                        last_name=last_name,
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
                        disambiguation_source=disambiguation_source,
                        put_code=put_code,
                        orcid=orcid,
                        local_id=local_id,
                        delete_record=delete_record,
                        url=val(row, 19),
                        display_index=val(row, 20),
                        visibility=visibility,
                        is_active=is_active,
                    )
                    validator = ModelValidator(af)
                    if not validator.validate():
                        raise ModelExceptionError(f"Invalid record: {validator.errors}")
                    af.save()

                    external_id_type = val(row, 21, "").lower()
                    external_id_relationship = val(row, 24)
                    if external_id_relationship:
                        external_id_relationship = external_id_relationship.replace(
                            "_", "-"
                        ).lower()
                    external_id_value = val(row, 22)

                    if external_id_type and external_id_value:

                        ae = AffiliationExternalId(
                            record=af,
                            type=external_id_type,
                            value=external_id_value,
                            url=val(row, 23),
                            relationship=external_id_relationship,
                        )

                        validator = ModelValidator(ae)
                        if not validator.validate():
                            raise ModelExceptionError(f"Invalid record: {validator.errors}")
                        ae.save()
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load affiliation file.")
                raise

        return task


class FundingRecord(RecordModel):
    """Funding record loaded from JSON file for batch processing."""

    funiding_type_choices = [(v, v.replace("-", " ").title()) for v in FUNDING_TYPES]

    task = ForeignKeyField(Task, backref="funding_records", on_delete="CASCADE")
    title = CharField(max_length=255)
    translated_title = CharField(null=True, max_length=255)
    translated_title_language_code = CharField(null=True, max_length=10, choices=language_choices)
    type = CharField(max_length=255, choices=funiding_type_choices)
    organization_defined_type = CharField(null=True, max_length=255)
    short_description = CharField(null=True, max_length=5000)
    amount = CharField(null=True, max_length=255)
    currency = CharField(null=True, max_length=3, choices=currency_choices)
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    org_name = CharField(null=True, max_length=255, verbose_name="Organisation Name")
    city = CharField(null=True, max_length=255)
    region = CharField(null=True, max_length=255)
    country = CharField(null=True, max_length=255, choices=country_choices)
    disambiguated_id = CharField(null=True)
    disambiguation_source = CharField(
        null=True, max_length=255, choices=disambiguation_source_choices
    )
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True
    )
    processed_at = DateTimeField(null=True)
    url = CharField(max_length=200, null=True)
    status = TextField(null=True, help_text="Record processing status.")

    def to_export_dict(self):
        """Map the funding record to dict for export into JSON/YAML."""
        d = super().to_export_dict()
        d["amount"] = {"currency-code": self.currency, "value": self.amount}
        return d

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source, newline="")
        if filename is None:
            filename = datetime.utcnow().isoformat(timespec="seconds")
        reader = csv.reader(source)
        header = next(reader)

        if len(header) == 1 and "\t" in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)

        if len(header) < 2:
            raise ModelExceptionError("Expected CSV or TSV format file.")

        header_rexs = [
            re.compile(ex, re.I)
            for ex in [
                "title$",
                r"translated\s+(title)?",
                r"translat(ed)?(ion)?\s+(title)?\s*lang(uage)?.*(code)?",
                "type$",
                r"org(ani[sz]ation)?\s*(defined)?\s*type",
                r"(short\s*|description\s*)+$",
                "amount",
                "currency",
                r"start\s*(date)?",
                r"end\s*(date)?",
                r"(org(gani[zs]ation)?)?\s*name$",
                "city",
                "region|state",
                "country",
                r"disambiguated\s*(org(ani[zs]ation)?)?\s*id(entifier)?",
                r"disambiguation\s+source$",
                r"(is)?\s*active$",
                r"orcid\s*(id)?$",
                "email",
                r"(external)?\s*id(entifier)?\s+type$",
                r"((external)?\s*id(entifier)?\s+value|funding.*id)$",
                r"(external)?\s*id(entifier)?\s*url",
                r"(external)?\s*id(entifier)?\s*rel(ationship)?",
                "put.*code",
                r"(is)?\s*visib(bility|le)?",
                r"first\s*(name)?",
                r"(last|sur)\s*(name)?",
                "local.*|.*identifier",
                r"url",
            ]
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column.strip()):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        if all(idx is None for idx in idxs):
            raise ModelExceptionError(
                f"Failed to map fields based on the header of the file: {header}"
            )

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, i, default=None):
            if len(idxs) <= i or idxs[i] is None or idxs[i] >= len(row):
                return default
            else:
                v = row[idxs[i]].strip()
            return default if v == "" else v

        rows = []
        cached_row = []
        is_enqueue = False
        for row_no, row in enumerate(reader):
            # skip empty lines:
            if len([item for item in row if item and item.strip()]) == 0:
                continue
            if len(row) == 1 and row[0].strip() == "":
                continue

            orcid, email = val(row, 17), normalize_email(val(row, 18, ""))
            orcid = validate_orcid_id(orcid)
            if email and not validators.email(email):
                raise ValueError(f"Invalid email address '{email}'  in the row #{row_no+2}: {row}")

            visibility = val(row, 24)
            if visibility:
                visibility = visibility.replace("_", "-").lower()

            invitee = dict(
                identifier=val(row, 27),
                email=email,
                first_name=val(row, 25),
                last_name=val(row, 26),
                orcid=orcid,
                put_code=val(row, 23),
                visibility=visibility,
            )

            title = val(row, 0)
            external_id_type = val(row, 19, "").lower()
            external_id_value = val(row, 20)
            external_id_relationship = val(row, 22, "").replace("_", "-").lower()

            if external_id_type not in EXTERNAL_ID_TYPES:
                raise ModelExceptionError(
                    f"Invalid External Id Type: '{external_id_type}', Use 'doi', 'issn' "
                    f"or one of the accepted types found here: https://pub.orcid.org/v3.0/identifiers"
                )

            if not external_id_value:
                raise ModelExceptionError(
                    f"Invalid External Id Value or Funding Id: {external_id_value}, #{row_no+2}: {row}."
                )

            if not title:
                raise ModelExceptionError(
                    f"Title is mandatory, #{row_no+2}: {row}. Header: {header}"
                )

            if external_id_relationship not in RELATIONSHIPS:
                raise ModelExceptionError(
                    f"Invalid External Id Relationship '{external_id_relationship}' as it is not one of the "
                    f"{RELATIONSHIPS}, #{row_no+2}: {row}."
                )

            if (
                cached_row
                and title.lower() == val(cached_row, 0).lower()
                and external_id_type.lower() == val(cached_row, 19).lower()
                and external_id_value.lower() == val(cached_row, 20).lower()
                and external_id_relationship.lower() == val(cached_row, 22).lower()
            ):
                row = cached_row
            else:
                cached_row = row

            is_active = val(row, 16, "").lower() in ["y", "yes", "1", "true"]
            if is_active:
                is_enqueue = is_active

            funding_type = val(row, 3)
            if not funding_type:
                raise ModelExceptionError(
                    f"Funding type is mandatory, #{row_no+2}: {row}. Header: {header}"
                )
            else:
                funding_type = funding_type.replace("_", "-").lower()

            # The uploaded country must be from ISO 3166-1 alpha-2
            country = val(row, 13)
            if country:
                try:
                    country = countries.lookup(country).alpha_2
                except Exception:
                    raise ModelExceptionError(
                        f" (Country must be 2 character from ISO 3166-1 alpha-2) in the row "
                        f"#{row_no+2}: {row}. Header: {header}"
                    )

            rows.append(
                dict(
                    funding=dict(
                        title=title,
                        translated_title=val(row, 1),
                        translated_title_language_code=val(row, 2),
                        type=funding_type,
                        organization_defined_type=val(row, 4),
                        short_description=val(row, 5),
                        amount=val(row, 6),
                        currency=val(row, 7),
                        start_date=PartialDate.create(val(row, 8)),
                        end_date=PartialDate.create(val(row, 9)),
                        org_name=val(row, 10) or org.name,
                        city=val(row, 11) or org.city,
                        region=val(row, 12) or org.region,
                        country=country or org.country,
                        url=val(row, 28),
                        is_active=is_active,
                        disambiguated_id=val(row, 14) or org.disambiguated_id,
                        disambiguation_source=val(row, 15, "").upper()
                        or org.disambiguation_source,
                    ),
                    invitee=invitee,
                    external_id=dict(
                        type=external_id_type,
                        value=external_id_value,
                        url=val(row, 21),
                        relationship=external_id_relationship,
                    ),
                )
            )

        with db.atomic() as transaction:
            try:
                task = Task.create(org=org, filename=filename, task_type=TaskType.FUNDING)
                for funding, records in groupby(rows, key=lambda row: row["funding"].items()):
                    records = list(records)

                    fr = cls(task=task, **dict(funding))
                    validator = ModelValidator(fr)
                    if not validator.validate():
                        raise ModelExceptionError(f"Invalid record: {validator.errors}")
                    fr.save()

                    for external_id in set(
                        tuple(r["external_id"].items())
                        for r in records
                        if r["external_id"]["type"] and r["external_id"]["value"]
                    ):
                        ei = ExternalId(record=fr, **dict(external_id))
                        ei.save()

                    for invitee in set(
                        tuple(r["invitee"].items()) for r in records if r["invitee"]["email"]
                    ):
                        rec = FundingInvitee(record=fr, **dict(invitee))
                        validator = ModelValidator(rec)
                        if not validator.validate():
                            raise ModelExceptionError(
                                f"Invalid invitee record: {validator.errors}"
                            )
                        rec.save()
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task

            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load funding file.")
                raise

    @classmethod
    def load_from_json(cls, source, filename=None, org=None, task=None):
        """Load data from JSON file or a string."""
        # import data from file based on its extension; either it is YAML or JSON
        data = load_yaml_json(filename=filename, source=source)
        records = data["records"] if isinstance(data, dict) else data

        for r in records:
            validation_source_data = copy.deepcopy(r)
            validation_source_data = del_none(validation_source_data)

            # Adding schema validation for funding
            validator = Core(
                source_data=validation_source_data,
                schema_files=[os.path.join(SCHEMA_DIR, "funding_schema.yaml")],
            )
            validator.validate(raise_exception=True)

        with db.atomic() as transaction:
            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                if not task:
                    task = Task.create(org=org, filename=filename, task_type=TaskType.FUNDING)
                else:
                    FundingRecord.delete().where(FundingRecord.task == task).execute()

                is_enqueue = False
                for r in records:

                    title = r.get("title", "title", "value")
                    translated_title = r.get("title", "translated-title", "value")
                    translated_title_language_code = r.get(
                        "title", "translated-title", "language-code"
                    )
                    rec_type = r.get("type")
                    if rec_type:
                        rec_type = rec_type.replace("_", "-").lower()
                    organization_defined_type = r.get("organization-defined-type", "value")
                    short_description = r.get("short-description")
                    amount = r.get("amount", "value")
                    url = r.get("url", "value")
                    currency = r.get("amount", "currency-code")
                    start_date = PartialDate.create(r.get("start-date"))
                    end_date = PartialDate.create(r.get("end-date"))
                    org_name = r.get("organization", "name")
                    city = r.get("organization", "address", "city")
                    region = r.get("organization", "address", "region")
                    country = r.get("organization", "address", "country")
                    disambiguated_id = r.get(
                        "organization",
                        "disambiguated-organization",
                        "disambiguated-organization-identifier",
                    )
                    disambiguation_source = r.get(
                        "organization", "disambiguated-organization", "disambiguation-source"
                    )
                    if disambiguation_source:
                        disambiguation_source = disambiguation_source.upper()

                    is_active = (
                        r.get("is-active").lower() in ["y", "yes", "1", "true"]
                        if r.get("is-active")
                        else False
                    )
                    if is_active:
                        is_enqueue = is_active

                    record = cls.create(
                        task=task,
                        title=title,
                        translated_title=translated_title,
                        translated_title_language_code=translated_title_language_code,
                        type=rec_type,
                        organization_defined_type=organization_defined_type,
                        short_description=short_description,
                        amount=amount,
                        currency=currency,
                        org_name=org_name,
                        city=city,
                        region=region,
                        country=country,
                        url=url,
                        is_active=is_active,
                        disambiguated_id=disambiguated_id,
                        disambiguation_source=disambiguation_source,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    invitees = r.get("invitees", default=[])
                    if invitees:
                        for invitee in invitees:
                            identifier = invitee.get("local-identifier") or invitee.get(
                                "identifier"
                            )
                            email = normalize_email(invitee.get("email"))
                            first_name = invitee.get("first-name")
                            last_name = invitee.get("last-name")
                            orcid = invitee.get_orcid("ORCID-iD")
                            put_code = invitee.get("put-code")
                            visibility = invitee.get("visibility")
                            if visibility:
                                visibility = visibility.replace("_", "-").lower()

                            FundingInvitee.create(
                                record=record,
                                identifier=identifier,
                                email=email,
                                first_name=first_name,
                                last_name=last_name,
                                orcid=orcid,
                                visibility=visibility,
                                put_code=put_code,
                            )
                    else:
                        raise SchemaError(
                            "Schema validation failed:\n - "
                            "Expecting Invitees for which the funding record will be written"
                        )

                    contributors = r.get("contributors", "contributor", default=[])
                    if contributors:
                        for contributor in contributors:
                            orcid = contributor.get_orcid("contributor-orcid", "path")
                            name = contributor.get("credit-name", "value")
                            email = normalize_email(contributor.get("contributor-email", "value"))
                            role = contributor.get("contributor-attributes", "contributor-role")

                            FundingContributor.create(
                                record=record, orcid=orcid, name=name, email=email, role=role
                            )

                    external_ids = r.get("external-ids", "external-id", default=[])
                    if external_ids:
                        for external_id in external_ids:
                            id_type = external_id.get("external-id-type")
                            value = external_id.get("external-id-value")
                            url = external_id.get("external-id-url", "value")
                            relationship = external_id.get("external-id-relationship")
                            if id_type:
                                id_type = id_type.lower()
                            if relationship:
                                relationship = relationship.replace("_", "-").lower()
                            ExternalId.create(
                                record=record,
                                type=id_type,
                                value=value,
                                url=url,
                                relationship=relationship,
                            )
                    else:
                        raise SchemaError(
                            "Schema validation failed:\n - An external identifier is required"
                        )
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task

            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load funding file.")
                raise

    class Meta:  # noqa: D101,D106
        table_alias = "fr"


class PeerReviewRecord(RecordModel):
    """Peer Review record loaded from Json file for batch processing."""

    subject_type_choices = [(v, v.replace("-", " ").title()) for v in SUBJECT_TYPES]
    reviewer_role_choices = [(v, v.title()) for v in REVIEWER_ROLES]

    task = ForeignKeyField(Task, backref="peer_review_records", on_delete="CASCADE")
    review_group_id = CharField(
        max_length=255, verbose_name="Group ID", help_text="Review Group ID"
    )
    reviewer_role = CharField(
        null=True,
        max_length=255,
        choices=reviewer_role_choices,
        verbose_name="Role",
        help_text="Reviewer Role",
    )
    review_url = CharField(null=True, max_length=255, verbose_name="URL", help_text="Review URL")
    review_type = CharField(
        null=True,
        max_length=255,
        choices=review_type_choices,
        verbose_name="Type",
        help_text="Review Type",
    )
    review_completion_date = PartialDateField(
        null=True, verbose_name="Completed On", help_text="Review Completion Date"
    )
    subject_external_id_type = CharField(
        null=True, max_length=255, verbose_name="Type", help_text="Subject External ID Type"
    )
    subject_external_id_value = CharField(
        null=True, max_length=255, verbose_name="Value", help_text="Subject External ID Value"
    )
    subject_external_id_url = CharField(
        null=True, max_length=255, verbose_name="URL", help_text="Subject External ID URL"
    )
    subject_external_id_relationship = CharField(
        null=True,
        max_length=255,
        choices=relationship_choices,
        verbose_name="Relationship",
        help_text="Subject External ID Relationship",
    )

    subject_container_name = CharField(
        null=True,
        max_length=255,
        verbose_name="Container Name",
        help_text="Subject Container Name",
    )
    subject_type = CharField(
        max_length=80,
        choices=subject_type_choices,
        null=True,
        verbose_name="Type",
        help_text="Subject Container Type",
    )
    subject_name_title = CharField(
        null=True, max_length=255, verbose_name="Title", help_text="Subject Name Title"
    )
    subject_name_subtitle = CharField(
        null=True, max_length=255, verbose_name="Subtitle", help_text="Subject Name Subtitle"
    )
    subject_name_translated_title_lang_code = CharField(
        null=True,
        max_length=10,
        verbose_name="Language",
        choices=language_choices,
        help_text="Subject Name Translated Title Lang Code",
    )
    subject_name_translated_title = CharField(
        null=True,
        max_length=255,
        verbose_name="Translated Title",
        help_text="Subject Name Translated Title",
    )
    subject_url = CharField(null=True, max_length=255)

    convening_org_name = CharField(
        null=True, max_length=255, verbose_name="Name", help_text="Convening Organisation "
    )
    convening_org_city = CharField(
        null=True, max_length=255, verbose_name="City", help_text="Convening Organisation City"
    )
    convening_org_region = CharField(
        null=True, max_length=255, verbose_name="Region", help_text="Convening Organisation Region"
    )
    convening_org_country = CharField(
        null=True,
        max_length=255,
        verbose_name="Country",
        choices=country_choices,
        help_text="Convening Organisation Country",
    )
    convening_org_disambiguated_identifier = CharField(
        null=True,
        max_length=255,
        verbose_name="Disambiguated Identifier",
        help_text="Convening Organisation Disambiguated Identifier",
    )
    convening_org_disambiguation_source = CharField(
        null=True,
        max_length=255,
        verbose_name="Disambiguation Source",
        help_text="Convening Organisation Disambiguation Source",
        choices=disambiguation_source_choices,
    )
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True
    )
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @property
    def title(self):
        """Title of the record."""
        return self.review_group_id

    @property
    def type(self):
        """Type of the record."""
        return self.review_type or self.subject_type or self.subject_external_id_type

    def key_name(self, name):
        """Map key-name to a model class key name for export."""
        if name == "external-ids":
            return "review-identifiers"
        return name

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source, newline="")
        if filename is None:
            filename = datetime.utcnow().isoformat(timespec="seconds")
        reader = csv.reader(source)
        header = next(reader)

        if len(header) == 1 and "\t" in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)

        if len(header) < 2:
            raise ModelExceptionError("Expected CSV or TSV format file.")

        header_rexs = [
            re.compile(ex, re.I)
            for ex in [
                r"review\s*group\s*id(entifier)?$",
                r"(reviewer)?\s*role$",
                r"review\s*url$",
                r"review\s*type$",
                r"(review\s*completion)?.*date",
                r"subject\s+external\s*id(entifier)?\s+type$",
                r"subject\s+external\s*id(entifier)?\s+value$",
                r"subject\s+external\s*id(entifier)?\s+url$",
                r"subject\s+external\s*id(entifier)?\s+rel(ationship)?$",
                r"subject\s+container\s+name$",
                r"(subject)?\s*type$",
                r"(subject)?\s*(name)?\s*title$",
                r"(subject)?\s*(name)?\s*subtitle$",
                r"(subject)?\s*(name)?\s*(translated)?\s*(title)?\s*lang(uage)?.*(code)?",
                r"(subject)?\s*(name)?\s*translated\s*title$",
                r"(subject)?\s*url$",
                r"(convening)?\s*org(ani[zs]ation)?\s*name$",
                r"(convening)?\s*org(ani[zs]ation)?\s*city",
                r"(convening)?\s*org(ani[zs]ation)?\s*region$",
                r"(convening)?\s*org(ani[zs]ation)?\s*country$",
                r"(convening)?\s*(org(ani[zs]ation)?)?\s*disambiguated\s*id(entifier)?",
                r"(convening)?\s*(org(ani[zs]ation)?)?\s*disambiguation\s*source$",
                "email",
                r"orcid\s*(id)?$",
                "local.*|identifier",
                r"first\s*(name)?",
                r"(last|sur)\s*(name)?",
                "put.*code",
                r"(is)?\s*visib(ility|le)?",
                r"(external)?\s*id(entifier)?\s+type$",
                r"((external)?\s*id(entifier)?\s+value|peer\s*review.*id)$",
                r"(external)?\s*id(entifier)?\s*url",
                r"(external)?\s*id(entifier)?\s*rel(ationship)?",
                r"(is)?\s*active$",
            ]
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column.strip()):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        if all(idx is None for idx in idxs):
            raise ModelExceptionError(
                f"Failed to map fields based on the header of the file: {header}"
            )

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, i, default=None):
            if len(idxs) <= i or idxs[i] is None or idxs[i] >= len(row):
                return default
            else:
                v = row[idxs[i]].strip()
            return default if v == "" else v

        rows = []
        cached_row = []
        is_enqueue = False
        for row_no, row in enumerate(reader):
            # skip empty lines:
            if len([item for item in row if item and item.strip()]) == 0:
                continue
            if len(row) == 1 and row[0].strip() == "":
                continue

            orcid, email = val(row, 23), normalize_email(val(row, 22, ""))
            orcid = validate_orcid_id(orcid)
            if email and not validators.email(email):
                raise ValueError(f"Invalid email address '{email}'  in the row #{row_no+2}: {row}")

            visibility = val(row, 28)
            if visibility:
                visibility = visibility.replace("_", "-").lower()

            invitee = dict(
                email=email,
                orcid=orcid,
                identifier=val(row, 24),
                first_name=val(row, 25),
                last_name=val(row, 26),
                put_code=val(row, 27),
                visibility=visibility,
            )

            review_group_id = val(row, 0)
            if not review_group_id:
                raise ModelExceptionError(
                    f"Review Group ID is mandatory, #{row_no+2}: {row}. Header: {header}"
                )

            external_id_type = val(row, 29, "").lower()
            external_id_value = val(row, 30)
            external_id_relationship = val(row, 32)

            if external_id_relationship:
                external_id_relationship = external_id_relationship.replace("_", "-").lower()

                if external_id_relationship not in RELATIONSHIPS:
                    raise ModelExceptionError(
                        f"Invalid External Id Relationship '{external_id_relationship}' as it is not one of the "
                        f"{RELATIONSHIPS}, #{row_no+2}: {row}."
                    )

            if external_id_type not in EXTERNAL_ID_TYPES:
                raise ModelExceptionError(
                    f"Invalid External Id Type: '{external_id_type}', Use 'doi', 'issn' "
                    f"or one of the accepted types found here: https://pub.orcid.org/v3.0/identifiers"
                )

            if not external_id_value:
                raise ModelExceptionError(
                    f"Invalid External Id Value or Peer Review Id: {external_id_value}, #{row_no+2}: {row}."
                )

            if (
                cached_row
                and review_group_id.lower() == val(cached_row, 0).lower()
                and external_id_type.lower() == val(cached_row, 29).lower()
                and external_id_value.lower() == val(cached_row, 30).lower()
                and external_id_relationship.lower() == val(cached_row, 32).lower()
            ):
                row = cached_row
            else:
                cached_row = row

            is_active = val(row, 33, "").lower() in ["y", "yes", "1", "true"]
            if is_active:
                is_enqueue = is_active

            convening_org_name = val(row, 16)
            convening_org_city = val(row, 17)
            convening_org_country = val(row, 19)

            if not (convening_org_name and convening_org_city and convening_org_country):
                raise ModelExceptionError(
                    f"Information about Convening Organisation (Name, City and Country) is mandatory, "
                    f"#{row_no+2}: {row}. Header: {header}"
                )

            # The uploaded country must be from ISO 3166-1 alpha-2
            if convening_org_country:
                try:
                    convening_org_country = countries.lookup(convening_org_country).alpha_2
                except Exception:
                    raise ModelExceptionError(
                        f" (Convening Org Country must be 2 character from ISO 3166-1 alpha-2) in the row "
                        f"#{row_no+2}: {row}. Header: {header}"
                    )

            reviewer_role = val(row, 1, "").replace("_", "-").lower() or None
            review_type = val(row, 3, "").replace("_", "-").lower() or None
            subject_type = val(row, 10, "").replace("_", "-").lower() or None
            subject_external_id_relationship = val(row, 8, "").replace("_", "-").lower() or None
            convening_org_disambiguation_source = val(row, 21, "").upper() or None
            subject_external_id_type = val(row, 5, "").lower() or None
            review_completion_date = val(row, 4) or None

            if review_completion_date:
                review_completion_date = PartialDate.create(review_completion_date)
            rows.append(
                dict(
                    peer_review=dict(
                        review_group_id=review_group_id,
                        reviewer_role=reviewer_role,
                        review_url=val(row, 2),
                        review_type=review_type,
                        review_completion_date=review_completion_date,
                        subject_external_id_type=subject_external_id_type,
                        subject_external_id_value=val(row, 6),
                        subject_external_id_url=val(row, 7),
                        subject_external_id_relationship=subject_external_id_relationship,
                        subject_container_name=val(row, 9),
                        subject_type=subject_type,
                        subject_name_title=val(row, 11),
                        subject_name_subtitle=val(row, 12),
                        subject_name_translated_title_lang_code=val(row, 13),
                        subject_name_translated_title=val(row, 14),
                        subject_url=val(row, 15),
                        convening_org_name=convening_org_name,
                        convening_org_city=convening_org_city,
                        convening_org_region=val(row, 18),
                        convening_org_country=convening_org_country,
                        convening_org_disambiguated_identifier=val(row, 20),
                        convening_org_disambiguation_source=convening_org_disambiguation_source,
                        is_active=is_active,
                    ),
                    invitee=invitee,
                    external_id=dict(
                        type=external_id_type,
                        value=external_id_value,
                        url=val(row, 31),
                        relationship=external_id_relationship,
                    ),
                )
            )

        with db.atomic() as transaction:
            try:
                task = Task.create(org=org, filename=filename, task_type=TaskType.PEER_REVIEW)
                for peer_review, records in groupby(
                    rows, key=lambda row: row["peer_review"].items()
                ):
                    records = list(records)

                    prr = cls(task=task, **dict(peer_review))
                    validator = ModelValidator(prr)
                    if not validator.validate():
                        raise ModelExceptionError(f"Invalid record: {validator.errors}")
                    prr.save()

                    for external_id in set(
                        tuple(r["external_id"].items())
                        for r in records
                        if r["external_id"]["type"] and r["external_id"]["value"]
                    ):
                        ei = PeerReviewExternalId(record=prr, **dict(external_id))
                        ei.save()

                    for invitee in set(
                        tuple(r["invitee"].items()) for r in records if r["invitee"]["email"]
                    ):
                        rec = PeerReviewInvitee(record=prr, **dict(invitee))
                        validator = ModelValidator(rec)
                        if not validator.validate():
                            raise ModelExceptionError(
                                f"Invalid invitee record: {validator.errors}"
                            )
                        rec.save()
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task

            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load peer review file.")
                raise

    @classmethod
    def load_from_json(cls, source, filename=None, org=None, task=None, **kwargs):
        """Load data from JSON file or a string."""
        # import data from file based on its extension; either it is YAML or JSON
        data_list = load_yaml_json(filename=filename, source=source)
        if not filename:
            if isinstance(data_list, dict):
                filename = data_list.get("filename")
            else:
                filename = (
                    "peer_review_" + datetime.utcnow().isoformat(timespec="seconds") + ".json"
                )
        if isinstance(data_list, dict):
            data_list = data_list.get("records")

        for data in data_list:
            validation_source_data = copy.deepcopy(data)
            validation_source_data = del_none(validation_source_data)

            validator = Core(
                source_data=validation_source_data,
                schema_files=[os.path.join(SCHEMA_DIR, "peer_review_schema.yaml")],
            )
            validator.validate(raise_exception=True)

        with db.atomic() as transaction:
            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                if task:
                    cls.delete().where(cls.task == task).execute()
                else:
                    task = Task.create(org=org, filename=filename, task_type=TaskType.PEER_REVIEW)

                is_enqueue = False
                for data in data_list:

                    review_group_id = data.get("review-group-id")
                    reviewer_role = data.get("reviewer-role")
                    if reviewer_role:
                        reviewer_role = reviewer_role.strip().replace("_", "-").lower()

                    review_url = data.get("review-url", "value")
                    review_type = data.get("review-type")
                    if review_type:
                        review_type = review_type.strip().replace("_", "-").lower()

                    review_completion_date = PartialDate.create(data.get("review-completion-date"))
                    subject_external_id_type = data.get(
                        "subject-external-identifier", "external-id-type"
                    )
                    if subject_external_id_type:
                        subject_external_id_type = subject_external_id_type.strip().lower()

                    subject_external_id_value = data.get(
                        "subject-external-identifier", "external-id-value"
                    )
                    subject_external_id_url = data.get(
                        "subject-external-identifier", "external-id-url", "value"
                    )
                    subject_external_id_relationship = data.get(
                        "subject-external-identifier", "external-id-relationship"
                    )
                    if subject_external_id_relationship:
                        subject_external_id_relationship = subject_external_id_relationship.replace(
                            "_", "-"
                        ).lower()

                    subject_container_name = data.get("subject-container-name", "value")
                    subject_type = data.get("subject-type")
                    if subject_type:
                        subject_type = subject_type.strip().replace("_", "-").lower()

                    subject_name_title = data.get("subject-name", "title", "value")
                    subject_name_subtitle = data.get("subject-name", "subtitle", "value")
                    subject_name_translated_title_lang_code = data.get(
                        "subject-name", "translated-title", "language-code"
                    )
                    subject_name_translated_title = data.get(
                        "subject-name", "translated-title", "value"
                    )
                    subject_url = data.get("subject-url", "value")
                    convening_org_name = data.get("convening-organization", "name")
                    convening_org_city = data.get("convening-organization", "address", "city")
                    convening_org_region = data.get("convening-organization", "address", "region")
                    convening_org_country = data.get(
                        "convening-organization", "address", "country"
                    )
                    convening_org_disambiguated_identifier = data.get(
                        "convening-organization",
                        "disambiguated-organization",
                        "disambiguated-organization-identifier",
                    )
                    convening_org_disambiguation_source = data.get(
                        "convening-organization",
                        "disambiguated-organization",
                        "disambiguation-source",
                    )
                    if convening_org_disambiguation_source:
                        convening_org_disambiguation_source = (
                            convening_org_disambiguation_source.upper()
                        )

                    is_active = (
                        data.get("is-active").lower() in ["y", "yes", "1", "true"]
                        if data.get("is-active")
                        else False
                    )
                    if is_active:
                        is_enqueue = is_active

                    record = cls.create(
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
                        convening_org_disambiguation_source=convening_org_disambiguation_source,
                        is_active=is_active,
                    )

                    invitee_list = data.get("invitees")
                    if invitee_list:
                        for invitee in invitee_list:
                            identifier = invitee.get("local-identifier") or invitee.get(
                                "identifier"
                            )
                            email = normalize_email(invitee.get("email"))
                            first_name = invitee.get("first-name")
                            last_name = invitee.get("last-name")
                            orcid_id = invitee.get("ORCID-iD")
                            put_code = invitee.get("put-code")
                            visibility = get_val(invitee, "visibility")
                            if visibility:
                                visibility = visibility.replace("_", "-").lower()

                            PeerReviewInvitee.create(
                                record=record,
                                identifier=identifier,
                                email=email,
                                first_name=first_name,
                                last_name=last_name,
                                orcid=orcid_id,
                                visibility=visibility,
                                put_code=put_code,
                            )
                    else:
                        raise SchemaError(
                            "Schema validation failed:\n - "
                            "Expecting Invitees for which the peer review record will be written"
                        )

                    external_ids_list = (
                        data.get("review-identifiers").get("external-id")
                        if data.get("review-identifiers")
                        else None
                    )
                    if external_ids_list:
                        for external_id in external_ids_list:
                            id_type = external_id.get("external-id-type")
                            if id_type:
                                id_type = id_type.lower()

                            value = external_id.get("external-id-value")
                            url = (
                                external_id.get("external-id-url").get("value")
                                if external_id.get("external-id-url")
                                else None
                            )
                            relationship = external_id.get("external-id-relationship")
                            if relationship:
                                relationship = relationship.replace("_", "-").lower()

                            PeerReviewExternalId.create(
                                record=record,
                                type=id_type,
                                value=value,
                                url=url,
                                relationship=relationship,
                            )
                    else:
                        raise SchemaError(
                            "Schema validation failed:\n - An external identifier is required"
                        )

                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task
            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load peer review file.")
                raise

    def to_export_dict(self):
        """Map the peer-review record to dict for export into JSON/YAML."""
        d = super().to_export_dict()
        d["review-type"] = self.review_type
        d["reviewer-role"] = self.reviewer_role
        if self.subject_external_id_relationship or self.subject_external_id_value:
            d["subject-external-identifier"] = {
                "external-id-type": self.subject_external_id_type,
                "external-id-value": self.subject_external_id_value,
                "external-id-url": {"value": self.subject_external_id_url},
                "external-id-relationship": self.subject_external_id_relationship,
            }
        if self.subject_container_name:
            d["subject-container-name"] = {"value": self.subject_container_name}
        if self.subject_type:
            d["subject-type"] = self.subject_type
        if self.review_completion_date:
            cd = self.review_completion_date.as_orcid_dict()
            d["review-completion-date"] = cd
        if self.review_url:
            d["review-url"] = {"value": self.review_url}
        if self.review_group_id:
            d["review-group-id"] = self.review_group_id
        if self.subject_name_title:
            sn = {"title": {"value": self.subject_name_title}}
            if self.subject_name_subtitle:
                sn["subtitle"] = {"value": self.subject_name_subtitle}
            if self.subject_name_translated_title:
                sn["translated-title"] = {"value": self.subject_name_translated_title}
                if self.subject_name_translated_title_lang_code:
                    sn["translated-title"][
                        "language-code"
                    ] = self.subject_name_translated_title_lang_code
            d["subject-name"] = sn
        if self.subject_url:
            d["subject-url"] = dict(value=self.subject_url)
        if self.convening_org_name:
            co = {
                "name": self.convening_org_name,
                "address": {
                    "city": self.convening_org_city,
                    "region": self.convening_org_region,
                    "country": self.convening_org_country,
                },
            }
            if self.convening_org_disambiguated_identifier:
                pass
                co["disambiguated-organization"] = {
                    "disambiguated-organization-identifier": self.convening_org_disambiguated_identifier,
                    "disambiguation-source": self.convening_org_disambiguation_source,
                }
            d["convening-organization"] = co
        return d

    class Meta:  # noqa: D101,D106
        table_alias = "pr"


class PropertyRecord(RecordModel):
    """Researcher Url record loaded from Json file for batch processing."""

    task = ForeignKeyField(Task, backref="property_records", on_delete="CASCADE")
    type = CharField(verbose_name="Property Type", choices=property_type_choices)
    display_index = IntegerField(null=True)
    name = CharField(
        null=True, max_length=255, verbose_name="Property Name", help_text="Website name."
    )
    value = CharField(
        max_length=255,
        verbose_name="Property Value",
        help_text="URL, Also known as, Keyword, Other ID, or Country value.",
    )
    email = CharField(max_length=120, null=True)
    first_name = CharField(max_length=120, null=True)
    last_name = CharField(max_length=120, null=True)
    orcid = OrcidIdField(null=True)
    put_code = IntegerField(null=True)
    visibility = CharField(null=True, max_length=100, choices=visibility_choices)
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True
    )
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None, file_property_type=None):
        """Load data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source, newline="")
        if filename is None:
            if hasattr(source, "name"):
                filename = source.name
            else:
                filename = datetime.utcnow().isoformat(timespec="seconds")
        reader = csv.reader(source)
        header = next(reader)

        if len(header) == 1 and "\t" in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)

        if len(header) < 2:
            raise ModelExceptionError("Expected CSV or TSV format file.")

        if len(header) < 4:
            raise ModelExceptionError(
                "Wrong number of fields. Expected at least 3 fields "
                "(email address or another unique identifier, name and/or value) "
                f"and property type. Read header: {header}"
            )

        header_rexs = [
            re.compile(ex, re.I)
            for ex in [
                r"(url)?.*name",
                r".*value|.*content|.*country",
                r"(display)?.*index",
                "email",
                r"first\s*(name)?",
                r"(last|sur)\s*(name)?",
                "orcid.*",
                r"put|code",
                r"(is)?\s*visib(bility|le)?",
                "(propery)?.*type",
                r"(is)?\s*active$",
            ]
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column.strip()):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        if all(idx is None for idx in idxs):
            raise ModelExceptionError(
                f"Failed to map fields based on the header of the file: {header}"
            )

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, i, default=None):
            if len(idxs) <= i or idxs[i] is None or idxs[i] >= len(row):
                return default
            else:
                v = row[idxs[i]].strip()
            return default if v == "" else v

        with db.atomic() as transaction:
            try:
                task = Task.create(org=org, filename=filename, task_type=TaskType.PROPERTY)
                is_enqueue = False
                for row_no, row in enumerate(reader):
                    # skip empty lines:
                    if len([item for item in row if item and item.strip()]) == 0:
                        continue
                    if len(row) == 1 and row[0].strip() == "":
                        continue

                    email = normalize_email(val(row, 3, ""))
                    orcid = validate_orcid_id(val(row, 6))

                    if not (email or orcid):
                        raise ModelExceptionError(
                            f"Missing user identifier (email address or ORCID iD) in the row "
                            f"#{row_no+2}: {row}. Header: {header}"
                        )

                    if email and not validators.email(email):
                        raise ValueError(
                            f"Invalid email address '{email}'  in the row #{row_no+2}: {row}"
                        )

                    value = val(row, 1, "")
                    first_name = val(row, 4)
                    last_name = val(row, 5)
                    property_type = val(row, 9) or file_property_type
                    is_active = val(row, 10, "").lower() in ["y", "yes", "1", "true"]
                    if is_active:
                        is_enqueue = is_active

                    if property_type:
                        property_type = property_type.strip().upper()

                    if not property_type or property_type not in PROPERTY_TYPES:
                        raise ModelExceptionError(
                            "Missing or incorrect property type. "
                            f"(expected: {','.join(PROPERTY_TYPES)}: {row}"
                        )
                    name = None
                    if property_type == "URL":
                        name = val(row, 0, "")
                        if not name:
                            raise ModelExceptionError(
                                f"Missing URL Name. For Researcher URL Name is expected: {row}."
                            )
                    elif property_type == "COUNTRY":
                        # The uploaded country must be from ISO 3166-1 alpha-2
                        if value:
                            try:
                                value = countries.lookup(value).alpha_2
                            except Exception:
                                raise ModelExceptionError(
                                    f" (Country must be 2 character from ISO 3166-1 alpha-2) in the row "
                                    f"#{row_no+2}: {row}. Header: {header}"
                                )

                    if not value:
                        raise ModelExceptionError(
                            "Wrong number of fields. Expected at least fields ( content or value or country and "
                            f"email address or another unique identifier): {row}"
                        )

                    visibility = val(row, 8)
                    if visibility:
                        visibility = visibility.replace("_", "-").lower()
                    rr = cls(
                        task=task,
                        type=property_type,
                        is_active=is_active,
                        name=name,
                        value=value,
                        display_index=val(row, 2),
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        orcid=orcid,
                        put_code=val(row, 7),
                        visibility=visibility,
                    )
                    validator = ModelValidator(rr)
                    if not validator.validate():
                        raise ModelExceptionError(f"Invalid record: {validator.errors}")
                    rr.save()
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load Researcher Url Record file.")
                raise

        return task

    @classmethod
    def load_from_json(
        cls,
        source,
        filename=None,
        org=None,
        task=None,
        skip_schema_validation=False,
        file_property_type=None,
    ):
        """Load data from JSON file or a string."""
        data = load_yaml_json(filename=filename, source=source)
        if not skip_schema_validation:
            if isinstance(data, dict):
                jsonschema.validate(data, schemas.property_task)
            else:
                jsonschema.validate(data, schemas.property_record_list)
        records = data["records"] if isinstance(data, dict) else data
        if isinstance(data, dict):
            records = data["records"]
            if not filename:
                filename = data.get("filename")
            task_type = data.get("taks-type")
            if not file_property_type and task_type:
                file_property_type = {
                    "RESEARCHER_URL": "URL",
                    "OTHER_NAME": "NAME",
                    "KEYWORD": "KEYWORD",
                    "COUNTRY": "COUNTRY",
                }.get(task_type)
        else:
            records = data
        with db.atomic() as transaction:
            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                if not task:
                    task = Task.create(org=org, filename=filename, task_type=TaskType.PROPERTY)
                else:
                    cls.delete().where(cls.task_id == task.id).execute()

                is_enqueue = False
                for r in records:

                    value = (
                        r.get("value")
                        or r.get("url", "value")
                        or r.get("url-value")
                        or r.get("content")
                        or r.get("country")
                    )
                    display_index = r.get("display-index")
                    property_type = r.get("type") or file_property_type
                    if property_type:
                        property_type = property_type.strip().upper()
                    email = normalize_email(r.get("email"))
                    first_name = r.get("first-name")
                    last_name = r.get("last-name")
                    orcid = r.get_orcid("ORCID-iD") or r.get_orcid("orcid")
                    put_code = r.get("put-code")
                    visibility = r.get("visibility")
                    if visibility:
                        visibility = visibility.replace("_", "-").lower()
                    is_active = bool(r.get("is-active"))
                    if is_active:
                        is_enqueue = is_active

                    if not property_type or property_type not in PROPERTY_TYPES:
                        raise ModelExceptionError(
                            "Missing or incorrect property type. "
                            f"(expected: {','.join(PROPERTY_TYPES)}: {r}"
                        )
                    name = None
                    if property_type == "URL":
                        name = r.get("name") or r.get("url-name")
                        if not name:
                            raise ModelExceptionError(
                                f"Missing URL Name. For Researcher URL Name is expected: {r}."
                            )
                    elif property_type == "COUNTRY":
                        # The uploaded country must be from ISO 3166-1 alpha-2
                        if value:
                            try:
                                value = countries.lookup(value).alpha_2
                            except Exception:
                                raise ModelExceptionError(
                                    f"(Country {value} must be 2 character from ISO 3166-1 alpha-2): {r}."
                                )
                    cls.create(
                        task=task,
                        type=property_type,
                        is_active=is_active,
                        name=name,
                        value=value,
                        display_index=display_index,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        orcid=orcid,
                        visibility=visibility,
                        put_code=put_code,
                    )

                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task

            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load Researcher property file.")
                raise

    def to_export_dict(self):
        """Map the property record to dict for export into JSON/YAML."""
        d = super().to_export_dict()
        d.update(
            self.to_dict(
                recurse=False, to_dashes=True, exclude=[PropertyRecord.type, PropertyRecord.task]
            )
        )
        return d

    class Meta:  # noqa: D101,D106
        table_alias = "pr"


class WorkRecord(RecordModel):
    """Work record loaded from Json file for batch processing."""

    task = ForeignKeyField(Task, backref="work_records", on_delete="CASCADE")
    title = CharField(max_length=255)
    subtitle = CharField(null=True, max_length=255)
    translated_title = CharField(null=True, max_length=255)
    translated_title_language_code = CharField(null=True, max_length=10, choices=language_choices)
    journal_title = CharField(null=True, max_length=255)
    short_description = CharField(null=True, max_length=5000)
    citation_type = CharField(null=True, max_length=255, choices=citation_type_choices)
    citation_value = CharField(null=True, max_length=32767)
    type = CharField(null=True, max_length=255, choices=work_type_choices)
    publication_date = PartialDateField(null=True)
    url = CharField(null=True, max_length=255)
    language_code = CharField(null=True, max_length=10, choices=language_choices)
    country = CharField(null=True, max_length=255, choices=country_choices)

    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True
    )
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source, newline="")
        if filename is None:
            filename = datetime.utcnow().isoformat(timespec="seconds")
        reader = csv.reader(source)
        header = next(reader)

        if len(header) == 1 and "\t" in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)

        if len(header) < 2:
            raise ModelExceptionError("Expected CSV or TSV format file.")

        header_rexs = [
            re.compile(ex, re.I)
            for ex in [
                "title$",
                r"sub.*(title)?$",
                r"translated\s+(title)?",
                r"translat(ed)?(ion)?\s+(title)?\s*lang(uage)?.*(code)?",
                r"journal",
                "type$",
                r"(short\s*|description\s*)+$",
                r"citat(ion)?.*type",
                r"citat(ion)?.*value",
                r"(publication)?.*date",
                r"(publ(ication?))?.*media.*(type)?",
                r"url",
                r"lang(uage)?.*(code)?",
                r"country",
                r"(is)?\s*active$",
                r"orcid\s*(id)?$",
                "email",
                r"(external)?\s*id(entifier)?\s+type$",
                r"((external)?\s*id(entifier)?\s+value|work.*id)$",
                r"(external)?\s*id(entifier)?\s*url",
                r"(external)?\s*id(entifier)?\s*rel(ationship)?",
                "put.*code",
                r"(is)?\s*visib(bility|le)?",
                r"first\s*(name)?",
                r"(last|sur)\s*(name)?",
                "local.*|.*identifier",
            ]
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column.strip()):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        if all(idx is None for idx in idxs):
            raise ModelExceptionError(
                f"Failed to map fields based on the header of the file: {header}"
            )

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, i, default=None):
            if len(idxs) <= i or idxs[i] is None or idxs[i] >= len(row):
                return default
            else:
                v = row[idxs[i]].strip()
            return default if v == "" else v

        rows = []
        cached_row = []
        is_enqueue = False
        for row_no, row in enumerate(reader):
            # skip empty lines:
            if len([item for item in row if item and item.strip()]) == 0:
                continue
            if len(row) == 1 and row[0].strip() == "":
                continue

            orcid, email = val(row, 15), normalize_email(val(row, 16))
            if orcid:
                orcid = validate_orcid_id(orcid)
            if email and not validators.email(email):
                raise ValueError(f"Invalid email address '{email}'  in the row #{row_no+2}: {row}")

            visibility = val(row, 22)
            if visibility:
                visibility = visibility.replace("_", "-").lower()

            invitee = dict(
                identifier=val(row, 25),
                email=email,
                first_name=val(row, 23),
                last_name=val(row, 24),
                orcid=orcid,
                put_code=val(row, 21),
                visibility=visibility,
            )

            title = val(row, 0)
            external_id_type = val(row, 17, "").lower()
            external_id_value = val(row, 18)
            external_id_relationship = val(row, 20, "").replace("_", "-").lower()

            if external_id_type not in EXTERNAL_ID_TYPES:
                raise ModelExceptionError(
                    f"Invalid External Id Type: '{external_id_type}', Use 'doi', 'issn' "
                    f"or one of the accepted types found here: https://pub.orcid.org/v3.0/identifiers"
                )

            if not external_id_value:
                raise ModelExceptionError(
                    f"Invalid External Id Value or Work Id: {external_id_value}, #{row_no+2}: {row}."
                )

            if not title:
                raise ModelExceptionError(
                    f"Title is mandatory, #{row_no+2}: {row}. Header: {header}"
                )

            if external_id_relationship not in RELATIONSHIPS:
                raise ModelExceptionError(
                    f"Invalid External Id Relationship '{external_id_relationship}' as it is not one of the "
                    f"{RELATIONSHIPS}, #{row_no+2}: {row}."
                )

            if (
                cached_row
                and title.lower() == val(cached_row, 0).lower()
                and external_id_type.lower() == val(cached_row, 17).lower()
                and external_id_value.lower() == val(cached_row, 18).lower()
                and external_id_relationship.lower() == val(cached_row, 20).lower()
            ):
                row = cached_row
            else:
                cached_row = row

            is_active = val(row, 14, "").lower() in ["y", "yes", "1", "true"]
            if is_active:
                is_enqueue = is_active

            work_type = val(row, 5, "").replace("_", "-").lower()
            if not work_type:
                raise ModelExceptionError(
                    f"Work type is mandatory, #{row_no+2}: {row}. Header: {header}"
                )

            # The uploaded country must be from ISO 3166-1 alpha-2
            country = val(row, 13)
            if country:
                try:
                    country = countries.lookup(country).alpha_2
                except Exception:
                    raise ModelExceptionError(
                        f" (Country must be 2 character from ISO 3166-1 alpha-2) in the row "
                        f"#{row_no+2}: {row}. Header: {header}"
                    )

            publication_date = val(row, 9)
            citation_type = val(row, 7)
            if citation_type:
                citation_type = citation_type.replace("_", "-").lower()

            if publication_date:
                publication_date = PartialDate.create(publication_date)
            rows.append(
                dict(
                    work=dict(
                        title=title,
                        subtitle=val(row, 1),
                        translated_title=val(row, 2),
                        translated_title_language_code=val(row, 3),
                        journal_title=val(row, 4),
                        type=work_type,
                        short_description=val(row, 6),
                        citation_type=citation_type,
                        citation_value=val(row, 8),
                        publication_date=publication_date,
                        url=val(row, 11),
                        language_code=val(row, 12),
                        country=country,
                        is_active=is_active,
                    ),
                    invitee=invitee,
                    external_id=dict(
                        type=external_id_type,
                        value=external_id_value,
                        url=val(row, 19),
                        relationship=external_id_relationship,
                    ),
                )
            )

        with db.atomic() as transaction:
            try:
                task = Task.create(org=org, filename=filename, task_type=TaskType.WORK)
                for work, records in groupby(rows, key=lambda row: row["work"].items()):
                    records = list(records)

                    wr = cls(task=task, **dict(work))
                    validator = ModelValidator(wr)
                    if not validator.validate():
                        raise ModelExceptionError(f"Invalid record: {validator.errors}")
                    wr.save()

                    for external_id in set(
                        tuple(r["external_id"].items())
                        for r in records
                        if r["external_id"]["type"] and r["external_id"]["value"]
                    ):
                        ei = WorkExternalId(record=wr, **dict(external_id))
                        ei.save()

                    for invitee in set(
                        tuple(r["invitee"].items()) for r in records if r["invitee"]["email"]
                    ):
                        rec = WorkInvitee(record=wr, **dict(invitee))
                        validator = ModelValidator(rec)
                        if not validator.validate():
                            raise ModelExceptionError(
                                f"Invalid invitee record: {validator.errors}"
                            )
                        rec.save()
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task

            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load work file.")
                raise

    @classmethod
    def load_from_json(cls, source, filename=None, org=None, task=None, **kwargs):
        """Load data from JSON file or a string."""
        # import data from file based on its extension; either it is YAML or JSON
        data = load_yaml_json(filename=filename, source=source)
        if not filename and isinstance(data, dict):
            filename = data.get("filename")
        if isinstance(data, dict):
            data = data.get("records")

        # TODO: validation of uploaded work file
        for r in data:
            validation_source_data = copy.deepcopy(r)
            validation_source_data = del_none(validation_source_data)

            # Adding schema validation for Work
            validator = Core(
                source_data=validation_source_data,
                schema_files=[os.path.join(SCHEMA_DIR, "work_schema.yaml")],
            )
            validator.validate(raise_exception=True)

        with db.atomic() as transaction:
            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                if not task:
                    task = Task.create(org=org, filename=filename, task_type=TaskType.WORK)

                is_enqueue = False
                for r in data:

                    title = r.get("title", "title", "value")
                    subtitle = r.get("title", "subtitle", "value")
                    translated_title = r.get("title", "translated-title", "value")
                    translated_title_language_code = r.get(
                        "title", "translated-title", "language-code"
                    )
                    journal_title = r.get("journal-title", "value")
                    short_description = r.get("short-description")
                    citation_type = r.get("citation", "citation-type")
                    if citation_type:
                        citation_type = citation_type.strip().replace("_", "-").lower()
                    citation_value = r.get("citation", "citation-value")
                    rec_type = r.get("type")
                    if rec_type:
                        rec_type = rec_type.strip().replace("_", "-").lower()
                    url = r.get("url", "value")
                    language_code = r.get("language-code")
                    country = r.get("country", "value")
                    is_active = (
                        r.get("is-active").lower() in ["y", "yes", "1", "true"]
                        if r.get("is-active")
                        else False
                    )
                    if is_active:
                        is_enqueue = is_active

                    publication_date = PartialDate.create(r.get("publication-date"))

                    record = WorkRecord.create(
                        task=task,
                        title=title,
                        subtitle=subtitle,
                        translated_title=translated_title,
                        translated_title_language_code=translated_title_language_code,
                        journal_title=journal_title,
                        short_description=short_description,
                        citation_type=citation_type,
                        citation_value=citation_value,
                        type=rec_type,
                        publication_date=publication_date,
                        url=url,
                        is_active=is_active,
                        language_code=language_code,
                        country=country,
                    )

                    validator = ModelValidator(record)
                    if not validator.validate():
                        raise ModelExceptionError(f"Invalid Work record: {validator.errors}")

                    invitee_list = r.get("invitees")
                    if invitee_list:
                        for invitee in invitee_list:
                            identifier = invitee.get("local-identifier") or invitee.get(
                                "identifier"
                            )
                            email = normalize_email(invitee.get("email"))
                            first_name = invitee.get("first-name")
                            last_name = invitee.get("last-name")
                            orcid = invitee.get_orcid("ORCID-iD")
                            put_code = invitee.get("put-code")
                            visibility = get_val(invitee, "visibility")
                            if visibility:
                                visibility = visibility.replace("_", "-").lower()

                            WorkInvitee.create(
                                record=record,
                                identifier=identifier,
                                email=email.lower(),
                                first_name=first_name,
                                last_name=last_name,
                                orcid=orcid,
                                visibility=visibility,
                                put_code=put_code,
                            )
                    else:
                        raise SchemaError(
                            "Schema validation failed:\n - "
                            "Expecting Invitees for which the work record will be written"
                        )

                    contributor_list = r.get("contributors", "contributor")
                    if contributor_list:
                        for contributor in contributor_list:
                            orcid = contributor.get_orcid("contributor-orcid", "path")
                            name = get_val(contributor, "credit-name", "value")
                            email = normalize_email(
                                get_val(contributor, "contributor-email", "value")
                            )
                            role = get_val(
                                contributor, "contributor-attributes", "contributor-role"
                            )
                            contributor_sequence = get_val(
                                contributor, "contributor-attributes", "contributor-sequence"
                            )

                            WorkContributor.create(
                                record=record,
                                orcid=orcid,
                                name=name,
                                email=email,
                                role=role,
                                contributor_sequence=contributor_sequence,
                            )

                    external_ids_list = (
                        r.get("external-ids").get("external-id") if r.get("external-ids") else None
                    )
                    if external_ids_list:
                        for external_id in external_ids_list:
                            id_type = external_id.get("external-id-type")
                            if id_type:
                                id_type = id_type.lower()
                            value = external_id.get("external-id-value")
                            url = get_val(external_id, "external-id-url", "value")
                            relationship = external_id.get("external-id-relationship")
                            if relationship:
                                relationship = relationship.replace("_", "-").lower()

                            WorkExternalId.create(
                                record=record,
                                type=id_type,
                                value=value,
                                url=url,
                                relationship=relationship,
                            )
                    else:
                        raise SchemaError(
                            "Schema validation failed:\n - An external identifier is required"
                        )

                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task
            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load work record file.")
                raise

    def to_export_dict(self):
        """Map the work record to dict for export into JSON/YAML."""
        d = super().to_export_dict()
        if self.journal_title:
            d["journal-title"] = dict(value=self.journal_title)
        d["short-description"] = self.short_description
        if self.publication_date:
            pd = self.publication_date.as_orcid_dict()
            d["publication-date"] = pd
        if self.url:
            d["url"] = self.url
        if self.citation_type or self.citation_value:
            d["citation"] = {
                "citation-type": self.citation_type,
                "citation-value": self.citation_value,
            }
        if self.country:
            d["country"] = dict(value=self.country)
        return d

    class Meta:  # noqa: D101,D106
        table_alias = "wr"


class ContributorModel(BaseModel):
    """Common model bits of the contributor records."""

    orcid = OrcidIdField(null=True)
    name = CharField(max_length=120, null=True)
    role = CharField(max_length=120, null=True)
    email = CharField(max_length=120, null=True)

    def to_export_dict(self):
        """Map the contributor record to dict for export into JSON/YAML."""
        d = {
            "contributor-email": dict(value=self.email),
            "credit-name": dict(value=self.name),
            "contributor-orcid": dict(path=self.orcid),
        }
        if self.role:
            d["contributor-attributes"] = {"contributor-role": self.role}
        return d


class WorkContributor(ContributorModel):
    """Researcher or contributor - related to work."""

    record = ForeignKeyField(WorkRecord, backref="contributors", on_delete="CASCADE")
    contributor_sequence = CharField(max_length=120, null=True)

    class Meta:  # noqa: D101,D106
        table_alias = "wc"

    def to_export_dict(self):
        """Map the contributor record to dict for export into JSON/YAML."""
        d = super().to_export_dict()
        if self.contributor_sequence:
            if "contributor-attributes" in d:
                d["contributor-attributes"].update(
                    {"contributor-sequence": self.contributor_sequence}
                )
            else:
                d["contributor-attributes"] = {"contributor-sequence": self.contributor_sequence}
        return d


class FundingContributor(ContributorModel):
    """Researcher or contributor - receiver of the funding."""

    record = ForeignKeyField(FundingRecord, backref="contributors", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        table_alias = "fc"


class Invitee(BaseModel):
    """Common model bits of the invitees records."""

    identifier = CharField(max_length=120, null=True, verbose_name="Local Identifier")
    email = CharField(max_length=120, null=True)
    orcid = OrcidIdField(null=True)
    first_name = CharField(max_length=120, null=True)
    last_name = CharField(max_length=120, null=True)
    put_code = IntegerField(null=True)
    visibility = CharField(null=True, max_length=100, choices=visibility_choices)
    status = TextField(null=True, help_text="Record processing status.")
    processed_at = DateTimeField(null=True)

    def to_export_dict(self):
        """Get row representation suitable for export to JSON/YAML."""
        c = self.__class__
        d = self.to_dict(
            to_dashes=True,
            exclude_nulls=True,
            only=[c.identifier, c.email, c.first_name, c.last_name, c.put_code, c.visibility],
            recurse=False,
        )
        if self.orcid:
            d["ORCID-iD"] = self.orcid
        return d

    class Meta:  # noqa: D101,D106
        table_alias = "i"


class PeerReviewInvitee(Invitee):
    """Researcher or Invitee - related to peer review."""

    record = ForeignKeyField(PeerReviewRecord, backref="invitees", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        table_alias = "pi"


class WorkInvitee(Invitee):
    """Researcher or Invitee - related to work."""

    record = ForeignKeyField(WorkRecord, backref="invitees", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        table_alias = "wi"


class FundingInvitee(Invitee):
    """Researcher or Invitee - related to funding."""

    record = ForeignKeyField(FundingRecord, backref="invitees", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        table_alias = "fi"


class ExternalIdModel(BaseModel):
    """Common model bits of the ExternalId records."""

    type = CharField(max_length=255, choices=external_id_type_choices)
    value = CharField(max_length=255)
    url = CharField(max_length=200, null=True)
    relationship = CharField(null=True, max_length=255, choices=relationship_choices)

    def to_export_dict(self):
        """Map the external ID record to dict for exprt into JSON/YAML."""
        d = {
            "external-id-type": self.type,
            "external-id-value": self.value,
            "external-id-relationship": self.relationship,
        }
        if self.url:
            d["external-id-url"] = {"value": self.url}
        return d


class WorkExternalId(ExternalIdModel):
    """Work ExternalId loaded for batch processing."""

    record = ForeignKeyField(WorkRecord, backref="external_ids", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        table_alias = "wei"


class PeerReviewExternalId(ExternalIdModel):
    """Peer Review ExternalId loaded for batch processing."""

    record = ForeignKeyField(PeerReviewRecord, backref="external_ids", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        table_alias = "pei"


# TODO: refacore to use many-to-many relation
class ExternalId(ExternalIdModel):
    """Funding ExternalId loaded for batch processing."""

    record = ForeignKeyField(FundingRecord, null=True, backref="external_ids", on_delete="CASCADE")

    class Meta:  # noqa: D101,D106
        table_alias = "ei"


class Resource(BaseModel):
    """Research resource."""

    title = CharField(max_length=1000)
    display_index = IntegerField(null=True)
    visibility = CharField(max_length=10, choices=visibility_choices)


class ResoureceExternalId(BaseModel):
    """Linkage between resoucrece and ExternalId."""

    external_id = ForeignKeyField(ExternalId, index=True, on_delete="CASCADE")
    resource = ForeignKeyField(Resource, index=True, on_delete="CASCADE")

    class Meta:  # noqa: D106
        table_alias = "rei"


class AffiliationExternalId(ExternalIdModel):
    """Affiliation ExternalId loaded for batch processing."""

    record = ForeignKeyField(AffiliationRecord, backref="external_ids", on_delete="CASCADE")

    def to_export_dict(self):
        """Map the external ID record to dict for exprt into JSON/YAML."""
        d = {
            "external-id-type": self.type,
            "external-id-value": self.value,
            "external-id-relationship": self.relationship,
            "external-id-url": self.url,
        }
        return d

    class Meta:  # noqa: D101,D106
        table_alias = "aei"


class OtherIdRecord(ExternalIdModel):
    """Other ID record loaded from json/csv file for batch processing."""

    task = ForeignKeyField(Task, backref="other_id_records", on_delete="CASCADE")
    display_index = IntegerField(null=True)
    email = CharField(max_length=120, null=True)
    first_name = CharField(max_length=120, null=True)
    last_name = CharField(max_length=120, null=True)
    orcid = OrcidIdField(null=True)
    put_code = IntegerField(null=True)
    visibility = CharField(null=True, max_length=100, choices=visibility_choices)
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True
    )
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source)
        if filename is None:
            if hasattr(source, "name"):
                filename = source.name
            else:
                filename = datetime.utcnow().isoformat(timespec="seconds")
        reader = csv.reader(source)
        header = next(reader)

        if len(header) == 1 and "\t" in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)

        if len(header) < 2:
            raise ModelExceptionError("Expected CSV or TSV format file.")

        if len(header) < 5:
            raise ModelExceptionError(
                "Wrong number of fields. Expected at least 5 fields "
                "(email address or another unique identifier, External ID Type, External ID Value, External ID URL, "
                f"External ID Relationship). Read header: {header}"
            )

        header_rexs = [
            re.compile(ex, re.I)
            for ex in (
                r"(display)?.*index",
                r"((external)?\s*id(entifier)?\s+type|.*type)$",
                r"((external)?\s*id(entifier)?\s+value|.*value)$",
                r"((external)?\s*id(entifier)?\s*url|.*url)$",
                r"((external)?\s*id(entifier)?\s*rel(ationship)?|.*relationship)$",
                "email",
                r"first\s*(name)?",
                r"(last|sur)\s*(name)?",
                "orcid.*",
                r"put|code",
                r"(is)?\s*visib(bility|le)?",
                r"(is)?\s*active$",
            )
        ]

        def index(rex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if rex.match(column.strip()):
                    return i
            else:
                return None

        idxs = [index(rex) for rex in header_rexs]

        if all(idx is None for idx in idxs):
            raise ModelExceptionError(
                f"Failed to map fields based on the header of the file: {header}"
            )

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, i, default=None):
            if len(idxs) <= i or idxs[i] is None or idxs[i] >= len(row):
                return default
            else:
                v = row[idxs[i]].strip()
            return default if v == "" else v

        with db.atomic() as transaction:
            try:
                task = Task.create(org=org, filename=filename, task_type=TaskType.OTHER_ID)
                is_enqueue = False
                for row_no, row in enumerate(reader):
                    # skip empty lines:
                    if len([item for item in row if item and item.strip()]) == 0:
                        continue
                    if len(row) == 1 and row[0].strip() == "":
                        continue

                    email = normalize_email(val(row, 5))
                    orcid = validate_orcid_id(val(row, 8))

                    if not (email or orcid):
                        raise ModelExceptionError(
                            f"Missing user identifier (email address or ORCID iD) in the row "
                            f"#{row_no+2}: {row}. Header: {header}"
                        )

                    if email and not validators.email(email):
                        raise ValueError(
                            f"Invalid email address '{email}'  in the row #{row_no+2}: {row}"
                        )

                    rec_type = val(row, 1, "").lower()
                    value = val(row, 2)
                    url = val(row, 3)
                    relationship = val(row, 4)
                    if relationship:
                        relationship = relationship.replace("_", "-").lower()
                    first_name = val(row, 6)
                    last_name = val(row, 7)
                    is_active = val(row, 11, "").lower() in ["y", "yes", "1", "true"]
                    if is_active:
                        is_enqueue = is_active

                    if rec_type not in EXTERNAL_ID_TYPES:
                        raise ModelExceptionError(
                            f"Invalid External Id Type: '{rec_type}', Use 'doi', 'issn' "
                            f"or one of the accepted types found here: https://pub.orcid.org/v3.0/identifiers"
                        )

                    if not value:
                        raise ModelExceptionError(
                            f"Missing External Id Value: {value}, #{row_no+2}: {row}."
                        )

                    visibility = val(row, 10)
                    if visibility:
                        visibility = visibility.replace("_", "-").lower()
                    rr = cls(
                        task=task,
                        type=rec_type,
                        url=url,
                        relationship=relationship,
                        value=value,
                        display_index=val(row, 0),
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        orcid=orcid,
                        put_code=val(row, 9),
                        visibility=visibility,
                        is_active=is_active,
                    )
                    validator = ModelValidator(rr)
                    if not validator.validate():
                        raise ModelExceptionError(f"Invalid record: {validator.errors}")
                    rr.save()
                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load Other IDs Record file.")
                raise

        return task

    @classmethod
    def load_from_json(
        cls, source, filename=None, org=None, task=None, skip_schema_validation=False
    ):
        """Load data from JSON file or a string."""
        data = load_yaml_json(filename=filename, source=source)
        if not skip_schema_validation:
            if isinstance(data, dict):
                jsonschema.validate(data, schemas.other_id_task)
            else:
                jsonschema.validate(data, schemas.other_id_record_list)
        records = data["records"] if isinstance(data, dict) else data
        with db.atomic() as transaction:
            try:
                if org is None:
                    org = current_user.organisation if current_user else None
                if not task:
                    task = Task.create(org=org, filename=filename, task_type=TaskType.OTHER_ID)

                is_enqueue = False
                for r in records:

                    id_type = r.get("type") or r.get("external-id-type")
                    if id_type:
                        id_type = id_type.lower()
                    value = r.get("value") or r.get("external-id-value")
                    url = (
                        r.get("url")
                        or r.get("external-id-url", "value")
                        or r.get("external-id-url")
                    )
                    relationship = r.get("relationship") or r.get("external-id-relationship")
                    if relationship:
                        relationship = relationship.replace("_", "-").lower()
                    display_index = r.get("display-index")
                    email = normalize_email(r.get("email"))
                    first_name = r.get("first-name")
                    last_name = r.get("last-name")
                    orcid = r.get_orcid("ORCID-iD") or r.get_orcid("orcid")
                    put_code = r.get("put-code")
                    visibility = r.get("visibility")
                    if visibility:
                        visibility = visibility.replace("_", "-").lower()
                    is_active = bool(r.get("is-active"))
                    if is_active:
                        is_enqueue = is_active

                    cls.create(
                        task=task,
                        type=id_type,
                        value=value,
                        url=url,
                        relationship=relationship,
                        display_index=display_index,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        orcid=orcid,
                        visibility=visibility,
                        put_code=put_code,
                        is_active=is_active,
                    )

                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
                return task

            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load Other IDs file.")
                raise

    class Meta:  # noqa: D101,D106
        table_alias = "oir"


class OrgRecord(RecordModel):
    """Common organisation record part of the batch processing reocords."""

    name = CharField(max_length=1000)
    city = TextField(null=True)
    region = TextField(verbose_name="State/Region", null=True)
    country = CharField(max_length=2, null=True, choices=country_choices)
    disambiguated_id = TextField(verbose_name="Disambiguation ORG Id", null=True)
    disambiguation_source = TextField(
        verbose_name="Disambiguation ORG Source", null=True, choices=disambiguation_source_choices
    )

    class Meta:  # noqa: D101,D106
        table_alias = "or"


class ResourceRecord(RecordModel, Invitee):
    """Research resource record."""

    display_index = IntegerField(null=True)
    task = ForeignKeyField(Task, backref="resource_records", on_delete="CASCADE")

    # Resource
    name = CharField(max_length=1000)
    type = CharField(max_length=1000, null=True)
    start_date = PartialDateField(null=True)
    end_date = PartialDateField(null=True)
    url = CharField(max_length=200, null=True)

    host_name = CharField(max_length=1000, verbose_name="Name", help_text="Resource Host Name")
    host_city = CharField(null=True, verbose_name="City", help_text="Resource Host City")
    host_region = CharField(
        max_length=300, null=True, verbose_name="Region", help_text="Resource Host Region"
    )
    host_country = CharField(
        max_length=2,
        null=True,
        choices=country_choices,
        verbose_name="Country",
        help_text="Resource Host Country",
    )
    host_disambiguated_id = CharField(
        null=True, verbose_name="Disambiguated ID", help_text="Resource Host Disambiguated ID"
    )
    host_disambiguation_source = CharField(
        null=True,
        choices=disambiguation_source_choices,
        verbose_name="Disambiguation Source",
        help_text="Resource Host Disambiguation Source",
    )

    external_id_type = CharField(
        max_length=255,
        choices=external_id_type_choices,
        verbose_name="Type",
        help_text="External ID Type",
    )
    external_id_value = CharField(
        max_length=255, verbose_name="Value", help_text="External ID Value"
    )
    external_id_url = CharField(
        max_length=200, null=True, verbose_name="URL", help_text="External ID URL"
    )
    external_id_relationship = CharField(
        null=True,
        max_length=255,
        choices=relationship_choices,
        verbose_name="Relationship",
        help_text="External ID Relationship",
    )

    # Proposal
    proposal_title = CharField(max_length=1000, verbose_name="Title", help_text="Proposal Title")
    proposal_start_date = PartialDateField(
        null=True, verbose_name="Start Date", help_text="Proposal Start Date"
    )
    proposal_end_date = PartialDateField(
        null=True, verbose_name="End Date", help_text="Proposal End Date"
    )
    proposal_url = CharField(
        max_length=200, null=True, verbose_name="URL", help_text="Proposal URL"
    )
    proposal_host_name = CharField(
        max_length=1000, verbose_name="Name", help_text="Proposal Host Name"
    )
    proposal_host_city = CharField(null=True, verbose_name="City", help_text="Proposal Host City")
    proposal_host_region = CharField(
        max_length=300, null=True, verbose_name="Region", help_text="Proposal Host Region"
    )
    proposal_host_country = CharField(
        max_length=2,
        null=True,
        choices=country_choices,
        verbose_name="City",
        help_text="Proposal Host City",
    )
    proposal_host_disambiguated_id = CharField(
        null=True, verbose_name="Disambiguated ID", help_text="Proposal Host Disambiguated ID"
    )
    proposal_host_disambiguation_source = CharField(
        null=True,
        choices=disambiguation_source_choices,
        verbose_name="Disabmiguation Source",
        help_text="Propasal Host Disambiguation Source",
    )
    proposal_external_id_type = CharField(
        max_length=255,
        choices=external_id_type_choices,
        verbose_name="Type",
        help_text="Proposal Externa ID Type",
    )
    proposal_external_id_value = CharField(
        max_length=255, verbose_name="Value", help_text="Proposal External ID Value"
    )
    proposal_external_id_url = CharField(
        max_length=200, null=True, verbose_name="URL", help_text="Proposal External ID URL"
    )
    proposal_external_id_relationship = CharField(
        null=True,
        max_length=255,
        choices=relationship_choices,
        verbose_name="Relationship",
        help_text="Proposal External ID Relationship",
    )

    is_active = BooleanField(
        default=False, help_text="The record is marked 'active' for batch processing", null=True
    )
    processed_at = DateTimeField(null=True)
    local_id = CharField(
        max_length=100,
        null=True,
        verbose_name="Local ID",
        help_text="Record identifier used in the data source system.",
    )

    visibility = CharField(null=True, max_length=100, choices=visibility_choices)
    status = TextField(null=True, help_text="Record processing status.")

    class Meta:  # noqa: D101,D106
        table_alias = "rr"

    @classmethod
    def load_from_csv(cls, source, filename=None, org=None):
        """Load data from CSV/TSV file or a string."""
        if isinstance(source, str):
            source = StringIO(source, newline="")
        if filename is None:
            filename = datetime.utcnow().isoformat(timespec="seconds") + (
                ".tsv" if "\t" in source else ".csv"
            )
        reader = csv.reader(source)
        header = next(reader)

        if len(header) == 1 and "\t" in header[0]:
            source.seek(0)
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)

        if len(header) < 2:
            raise ModelExceptionError("Expected CSV or TSV format file.")

        header_rexs = [
            (re.compile(ex, re.I), c)
            for (ex, c) in [
                (r"local.*|.*identifier", "identifier"),
                (r"email", "email"),
                (r"orcid\s*id", "orcid"),
                (r"first\s*name", "first_name"),
                (r"last\s*name", "last_name"),
                (r"put\s*code", "put_code"),
                (r"visibility", "visibility"),
                (r"proposal\s*title", "proposal_title"),
                (r"proposal\s*start\s*date", "proposal_start_date"),
                (r"proposal\s*end\s*date", "proposal_end_date"),
                (r"proposal\s*url", "proposal_url"),
                (r"proposal\s*external\s*id\s*type", "proposal_external_id_type"),
                (r"proposal\s*external\s*id\s*value", "proposal_external_id_value"),
                (r"proposal\s*external\s*id\s*url", "proposal_external_id_url"),
                (r"proposal\s*external\s*id\s*relationship", "proposal_external_id_relationship"),
                (r"proposal\s*host\s*name", "proposal_host_name"),
                (r"proposal\s*host\s*city", "proposal_host_city"),
                (r"proposal\s*host\s*region", "proposal_host_region"),
                (r"proposal\s*host\s*country", "proposal_host_country"),
                (r"proposal\s*host\s*disambiguat.*id", "proposal_host_disambiguated_id"),
                (r"proposal\s*host\s*disambiguat.*source", "proposal_host_disambiguation_source"),
                (r"resource\s*name", "name"),
                (r"resource\s*type", "type"),
                (r"(resource\s*)?external\s*id\s*type", "external_id_type"),
                (r"(resource\s*)?external\s*id\s*value", "external_id_value"),
                (r"(resource\s*)?external\s*id\s*url", "external_id_url"),
                (r"(resource\s*)?external\s*id\s*relationship", "external_id_relationship"),
                (r"(resource\s*)?host\s*name", "host_name"),
                (r"(resource\s*)?host\s*city", "host_city"),
                (r"(resource\s*)?host\s*region", "host_region"),
                (r"(resource\s*)?host\s*country", "host_country"),
                (r"(resource\s*)?host\s*disambiguat.*id", "host_disambiguated_id"),
                (r"(resource\s*)?host\s*disambiguat.*source", "host_disambiguation_source"),
            ]
        ]

        def index(ex):
            """Return first header column index matching the given regex."""
            for i, column in enumerate(header):
                if ex.match(column.strip()):
                    return i
            else:
                return None

        # model column -> file column map:
        idxs = {column: index(ex) for ex, column in header_rexs}

        if all(idx is None for idx in idxs):
            raise ModelExceptionError(
                f"Failed to map fields based on the header of the file: {header}"
            )

        if org is None:
            org = current_user.organisation if current_user else None

        def val(row, column, default=None):
            idx = idxs.get(column)
            if idx is None or idx < 0 or idx >= len(row):
                return default
            return row[idx].strip() or default

        def country_code(row, column):
            country = val(row, column)
            if country:
                try:
                    country = countries.lookup(country).alpha_2
                except Exception:
                    raise ModelExceptionError(
                        f" (Country must be 2 character from ISO 3166-1 alpha-2) in the row "
                        f"#{row_no+2}: {row}. Header: {header}"
                    )
            return country

        with db.atomic() as transaction:
            try:
                task = Task.create(org=org, filename=filename, task_type=TaskType.RESOURCE)
                for row_no, row in enumerate(reader):
                    # skip empty lines:
                    if len([item for item in row if item and item.strip()]) == 0:
                        continue
                    if len(row) == 1 and row[0].strip() == "":
                        continue

                    orcid, email = val(row, "orcid"), normalize_email(val(row, "email"))
                    if orcid:
                        orcid = validate_orcid_id(orcid)
                    if email and not validators.email(email):
                        raise ValueError(
                            f"Invalid email address '{email}'  in the row #{row_no+2}: {row}"
                        )

                    visibility = val(row, "visibility")
                    if visibility:
                        visibility = visibility.lower()

                    rec = cls.create(
                        task=task,
                        visibility=visibility,
                        email=email,
                        orcid=orcid,
                        **{
                            c: v
                            for c, v in (
                                (c, val(row, c))
                                for c in idxs
                                if c not in ["email", "orcid", "visibility"]
                            )
                            if v
                        },
                    )
                    validator = ModelValidator(rec)
                    # TODO: removed the exclude paramtere after we sortout the
                    # valid domain values.
                    if not validator.validate(
                        exclude=[cls.external_id_relationship, cls.visibility]
                    ):
                        raise ValueError(
                            f"Invalid data in the row #{row_no+2}: {validator.errors}"
                        )

                transaction.commit()
                return task

            except Exception:
                transaction.rollback()
                app.logger.exception("Failed to load work file.")
                raise

        if task.is_ready:
            from .utils import enqueue_task_records

            enqueue_task_records(task)

        return task

    @property
    def orcid_research_resource(self):
        """Map the common record parts to dict representation of ORCID API V3.x research resource."""
        d = {}
        # resource-item
        host_org = {"name": self.host_name}
        if self.host_city or self.host_region or self.host_country:
            host_org["address"] = {
                "city": self.host_city,
                "region": self.host_region,
                "country": self.host_country,
            }
        if self.host_disambiguated_id:
            host_org["disambiguated-organization"] = {
                "disambiguated-organization-identifier": self.host_disambiguated_id,
                "disambiguation-source": self.host_disambiguation_source,
            }
        item = {
            "resource-name": self.name,
            "resource-type": self.type,
            "hosts": {"organization": [host_org]},
            "external-ids": {"external-id": [self.orcid_external_id()]},
        }
        if self.url:
            item["url"] = dict(value=self.url)
        d["resource-item"] = [item]

        # proposal
        host_org = {"name": self.proposal_host_name}
        if self.proposal_host_city or self.proposal_host_region or self.proposal_host_country:
            host_org["address"] = {
                "city": self.proposal_host_city,
                "region": self.proposal_host_region,
                "country": self.proposal_host_country,
            }
        if self.proposal_host_disambiguated_id:
            host_org["disambiguated-organization"] = {
                "disambiguated-organization-identifier": self.proposal_host_disambiguated_id,
                "disambiguation-source": self.proposal_host_disambiguation_source,
            }
        d["proposal"] = {
            "title": {"title": {"value": self.proposal_title}},
            "hosts": {"organization": [host_org]},
            "external-ids": {
                "external-id": [
                    self.orcid_external_id(
                        self.proposal_external_id_type,
                        self.proposal_external_id_value,
                        self.proposal_external_id_url,
                        self.proposal_external_id_relationship,
                    )
                ]
            },
            "start-date": self.proposal_start_date.as_orcid_dict(),
            "end-date": self.proposal_end_date.as_orcid_dict(),
        }
        if self.proposal_url:
            d["proposal"]["url"] = dict(value=self.proposal_url)
        if self.display_index:
            d["display-index"] = self.display_index
        if self.visibility:
            d["visibility"] = self.visibility.lower()
        if self.put_code:
            d["put-code"] = self.put_code
        return d

    def to_export_dict(self):
        """Map the funding record to dict for export into JSON/YAML."""
        d = self.orcid_research_resource
        d["invitees"] = [Invitee.to_export_dict(self)]
        return d

    @classmethod
    def load(
        cls,
        data,
        task=None,
        task_id=None,
        filename=None,
        override=True,
        skip_schema_validation=False,
        org=None,
    ):
        """Load ORCID message record task form JSON/YAML."""
        return MessageRecord.load(
            data,
            filename=filename,
            override=True,
            skip_schema_validation=True,
            org=org or current_user.organisation,
            task=task,
            task_id=task_id,
            task_type=TaskType.RESOURCE,
            version="3.0",
        )


# ThroughDeferred = DeferredThroughModel()


class MessageRecord(RecordModel):
    """ORCID message loaded from structured batch task file."""

    task = ForeignKeyField(Task, backref="message_records", on_delete="CASCADE")
    version = CharField(null=True)
    # type = CharField()
    message = TextField()
    # invitees = ManyToManyField(Invitee, backref="records", through_model=ThroughDeferred)
    invitees = ManyToManyField(Invitee, backref="records", on_delete="CASCADE")
    is_active = BooleanField(
        default=False, help_text="The record is marked for batch processing", null=True
    )
    # indicates that all ivitees (user profiles) were processed
    processed_at = DateTimeField(null=True)
    status = TextField(null=True, help_text="Record processing status.")

    @classmethod
    def load(
        cls,
        data,
        task=None,
        task_id=None,
        filename=None,
        override=True,
        skip_schema_validation=False,
        org=None,
        task_type=None,
        version="3.0",
    ):
        """Load ORCID message record task form JSON/YAML."""
        data = load_yaml_json(filename=filename, source=data)
        if org is None:
            org = current_user.organisation if current_user else None
        # if not skip_schema_validation:
        #     jsonschema.validate(data, schemas.affiliation_task)
        if not task and task_id:
            task = Task.select().where(Task.id == task_id).first()
        if not task and "id" in data and override and task_type:
            task_id = int(data["id"])
            task = (
                Task.select()
                .where(Task.id == task_id, Task.task_type == task_type, Task.is_raw)
                .first()
            )
        if not filename:
            if isinstance(data, dict):
                filename = data.get("filename")
            if not filename:
                filename = datetime.utcnow().isoformat(timespec="seconds")
        if task and not task_type:
            task_type = task.task_type
        if not task_type and isinstance(data, dict) and "type" in data:
            task_type = TaskType[data["type"].upper()]

        if isinstance(data, dict):
            records = data.get("records")
        else:
            records = data

        with db.atomic() as transaction:
            try:
                if not task:
                    task = Task.create(
                        org=org, filename=filename, task_type=task_type, is_raw=True
                    )
                elif override:
                    task.record_model.delete().where(task.record_model.task == task).execute()

                is_enqueue = False

                for r in records:
                    invitees = r.get("invitees")
                    if not invitees:
                        raise ModelExceptionError(
                            f"Missing invitees, expected to have at lease one: {r}"
                        )
                    del r["invitees"]

                    rec_id = r.get("id")
                    if rec_id:
                        rec_id = int(rec_id)
                        del r["id"]

                    is_active = r.get("is-active")
                    if "is-active" in r:
                        del r["is-active"]

                    message = json.dumps(r, indent=2)
                    if rec_id and not override:
                        rec = cls.get(int(rec_id))
                        if rec.message != message:
                            rec.message = message
                        if rec.version != version:
                            rec.version = version
                        rec.is_active = is_active
                    else:
                        rec = cls.create(
                            task=task, version=version, message=message, is_active=is_active
                        )
                    rec.invitees.add(
                        [
                            Invitee.create(
                                orcid=i.get("ORCID-iD"),
                                email=i.get("email"),
                                first_name=i.get("first-name"),
                                last_name=i.get("last-name"),
                                put_code=i.get("put-code"),
                                visibility=i.get("visibility"),
                            )
                            for i in invitees
                        ]
                    )

                if is_enqueue:
                    from .utils import enqueue_task_records

                    enqueue_task_records(task)
            except:
                transaction.rollback()
                app.logger.exception("Failed to load affiliation record task file.")
                raise
        return task

    def to_export_dict(self):
        """Map the common record parts to dict for export into JSON/YAML."""
        return self.to_dict()

    def to_dict(self, *args, **kwargs):
        """Map the common record parts to dict."""
        d = json.loads(self.message)
        d["id"] = self.id
        d["invitees"] = [i.to_export_dict() for i in self.invitees]
        return d


RecordInvitee = MessageRecord.invitees.get_through_model()


class Delegate(BaseModel):
    """External applications that can be redirected to."""

    hostname = CharField()


class Url(AuditedModel):
    """Shortened URLs."""

    short_id = CharField(unique=True, max_length=5)
    url = TextField()

    @classmethod
    def shorten(cls, url):
        """Create a shorten URL or retrieves an exiting one."""
        try:
            u = cls.get(url=url)
        except cls.DoesNotExist:
            while True:
                short_id = "".join(
                    random.choice(string.ascii_letters + string.digits) for _ in range(5)
                )
                if not cls.select().where(cls.short_id == short_id).exists():
                    break
            u = cls.create(short_id=short_id, url=url)
            return u
        return u


class Funding(BaseModel):
    """Uploaded research Funding record."""

    short_id = CharField(unique=True, max_length=5)
    url = TextField()


class Client(AuditedModel):
    """API Client Application/Consumer.

    A client is the app which wants to use the resource of a user.
    It is suggested that the client is registered by a user on your site,
    but it is not required.
    """

    name = CharField(null=True, max_length=40, help_text="human readable name, not required")
    homepage_url = CharField(null=True, max_length=100)
    description = CharField(
        null=True, max_length=400, help_text="human readable description, not required"
    )
    user = ForeignKeyField(
        User, null=True, on_delete="SET NULL", help_text="creator of the client, not required"
    )
    org = ForeignKeyField(Organisation, on_delete="CASCADE", backref="client_applications")

    client_id = CharField(max_length=100, unique=True)
    client_secret = CharField(max_length=55, unique=True)
    is_confidential = BooleanField(null=True, help_text="public or confidential")
    grant_type = CharField(max_length=18, default="client_credentials", null=True)
    response_type = CharField(max_length=4, default="code", null=True)

    _redirect_uris = TextField(null=True)
    _default_scopes = TextField(null=True)

    def save(self, *args, **kwargs):  # noqa: D102
        if self.is_dirty() and not getattr(self, "user_id") and current_user:
            self.user_id = current_user.id
        return super().save(*args, **kwargs)

    @property
    def client_type(self):  # noqa: D102
        if self.is_confidential:
            return "confidential"
        return "public"

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

    def __str__(self):  # noqa: D102
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
    client = ForeignKeyField(Client, index=True, on_delete="CASCADE")
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
            self._scopes = " ".join(value)


class Token(BaseModel):
    """Bearer Token.

    A bearer token is the final token that could be used by the client.
    There are other token types, but bearer token is widely used.
    Flask-OAuthlib only comes with a bearer token.
    """

    client = ForeignKeyField(Client, index=True, on_delete="CASCADE")
    user = ForeignKeyField(User, null=True, index=True, on_delete="SET NULL")
    token_type = CharField(max_length=40)

    access_token = CharField(max_length=100, unique=True)
    refresh_token = CharField(max_length=100, unique=True, null=True)
    created_at = DateTimeField(default=datetime.utcnow, null=True)
    expires_in = IntegerField(null=True)
    expires = DateTimeField(null=True, index=True)
    _scopes = TextField(null=True)

    @property
    def scopes(self):  # noqa: D102
        if self._scopes:
            return self._scopes.split()
        return []

    @property
    def expires_at(self):  # noqa: D102
        return self.expires


class AsyncOrcidResponse(BaseModel):
    """Asynchronouly invoked ORCID API calls."""

    job_id = UUIDField(primary_key=True)
    enqueued_at = DateTimeField(default=datetime.utcnow)
    executed_at = DateTimeField(null=True)
    method = CharField(max_length=10)
    url = CharField(max_length=200)
    status_code = SmallIntegerField(null=True)
    headers = TextField(null=True)
    body = TextField(null=True)


class MailLog(BaseModel):
    """Email log - the log of email sent from the Hub."""

    sent_at = DateTimeField(default=datetime.utcnow)
    org = ForeignKeyField(Organisation, null=True)
    recipient = CharField()
    sender = CharField()
    subject = CharField()
    was_sent_successfully = BooleanField(null=True)
    error = TextField(null=True)
    token = CharField(max_length=10)


DeferredForeignKey.resolve(User)


def readup_file(input_file):
    """Read up the whole content and decode it and return the whole content."""
    raw = input_file.read()
    detected_encoding = chardet.detect(raw).get("encoding")
    encoding_list = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1"]
    if detected_encoding:
        encoding_list.insert(0, detected_encoding)

    for encoding in encoding_list:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue


def create_tables(safe=True, drop=False):
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
        Log,
        AffiliationRecord,
        AffiliationExternalId,
        GroupIdRecord,
        OrgInvitation,
        Url,
        UserInvitation,
        FundingRecord,
        WorkRecord,
        WorkContributor,
        WorkExternalId,
        WorkInvitee,
        FundingContributor,
        FundingInvitee,
        ExternalId,
        PeerReviewRecord,
        PeerReviewInvitee,
        PeerReviewExternalId,
        OtherIdRecord,
        PropertyRecord,
        Client,
        Grant,
        Token,
        Delegate,
        AsyncOrcidResponse,
        MessageRecord,
        Invitee,
        RecordInvitee,
        ResourceRecord,
        MailLog,
    ]:

        model.bind(db)
        if drop and model.table_exists():
            model.drop_table()
        if not model.table_exists():
            model.create_table(safe=safe)


def create_audit_tables():
    """Create all DB audit tables for PostgreSQL DB."""
    try:
        db.connect()
    except OperationalError:
        pass

    if isinstance(db, PostgresqlDatabase):
        with open(
            os.path.join(os.path.dirname(__file__), "sql", "auditing.sql"), "br"
        ) as input_file:
            sql = readup_file(input_file)
            db.commit()
            with db.cursor() as cr:
                cr.execute(sql)
            db.commit()


def drop_tables():
    """Drop all model tables."""
    if isinstance(db, SqliteDatabase):
        foreign_keys = db.pragma("foreign_keys")
        db.pragma("foreign_keys", 0)

    for m in (
        File,
        User,
        UserOrg,
        OrcidToken,
        UserOrgAffiliation,
        OrgInfo,
        OrgInvitation,
        OrcidApiCall,
        OrcidAuthorizeCall,
        OtherIdRecord,
        FundingContributor,
        FundingInvitee,
        FundingRecord,
        PropertyRecord,
        PeerReviewInvitee,
        PeerReviewExternalId,
        PeerReviewRecord,
        WorkInvitee,
        WorkExternalId,
        WorkContributor,
        WorkRecord,
        AffiliationRecord,
        AffiliationExternalId,
        ExternalId,
        Url,
        UserInvitation,
        Task,
        Organisation,
    ):
        m.bind(db)
        if m.table_exists():
            try:
                m.drop_table(
                    fail_silently=True,
                    safe=True,
                    cascade=hasattr(db, "drop_cascade") and db.drop_cascade,
                )
            except OperationalError:
                pass
    if isinstance(db, SqliteDatabase):
        db.pragma("foreign_keys", foreign_keys)


def load_yaml_json(filename=None, source=None, content_type=None):
    """Create a common way of loading JSON or YAML file."""
    if not content_type:
        _, ext = os.path.splitext(filename or "")
        if not ext:
            source = source.strip()
        content_type = (
            "json"
            if ((not ext and (source.startswith("[") or source.startswith("{"))) or ext == ".json")
            else "yaml"
        )

    if content_type == "yaml":
        data = json.loads(json.dumps(yaml.load(source)), object_pairs_hook=NestedDict)
    else:
        data = json.loads(source, object_pairs_hook=NestedDict)

    # Removing None for correct schema validation
    if not isinstance(data, list) and not (isinstance(data, dict) and "records" in data):
        raise SchemaError("Schema validation failed:\n - Expecting a list of Records")
    return data


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
    if isinstance(d, NestedDict):
        return d.get(*keys, default=default)
    for k in keys:
        if not d:
            break
        d = d.get(k, default)
    return d


@lru_cache()
def audit_models():
    """Inrospects the audit trail table models."""
    # return generate_models(db, schema="audit") if isinstance(db, PostgresqlDatabase) else {}
    return {}
