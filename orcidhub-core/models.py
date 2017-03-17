from peewee import Model, CharField, BooleanField, SmallIntegerField, ForeignKeyField, TextField, CompositeKey
from peewee import drop_model_tables, OperationalError
from application import db
from enum import IntFlag
from flask_login import UserMixin

class Role(IntFlag):
    """
    Enum used to represent user role.
    The model provide multi role support
    representing role sets as bitmaps.
    """
    NONE = 0  # NONE
    SUPERUSER = 1  # SuperUser
    ADMIN = 2  # Admin
    RESEARCHER = 4  # Researcher
    ANY = 255  # ANY

    def __eq__(self, other):
        return (self.name == other or
                self.name == getattr(other, 'name', None))

    def __hash__(self):
        return hash(self.name)

class BaseModel(Model):

    class Meta:
        database = db

class Organisation(BaseModel):
    """
    Research oranisation
    """
    name = CharField(max_length=100, unique=True)
    email = CharField(max_length=80, unique=True, null=True)
    tuakiri_name = CharField(max_length=80, unique=True, null=True)
    orcid_client_id = CharField(max_length=80, unique=True, null=True)
    orcid_secret = CharField(max_length=80, unique=True, null=True)
    confirmed = BooleanField(default=False)

class User(BaseModel, UserMixin):
    """
    ORCiD Hub user (incling researchers, organisation administrators,
    hub administrators, etc.)
    """
    name = CharField(max_length=64, null=True)
    first_name = CharField(null=True, verbose_name="Firs Name")
    last_name = CharField(null=True, verbose_name="Last Name")
    email = CharField(max_length=120, unique=True, null=True)
    edu_person_shared_token = CharField(max_length=120, unique=True, verbose_name="EDU Person Shared Token", null=True)
    # ORCiD:
    orcid = CharField(max_length=120, unique=True, verbose_name="ORCID", null=True)
    access_token = CharField(max_length=120, unique=True, null=True)
    token_type = TextField(null=True)
    refresh_token = TextField(null=True)
    confirmed = BooleanField(default=False)
    # Role bit-map:
    roles = SmallIntegerField(default=0)
    # TODO: many-to-many
    organisation = ForeignKeyField(Organisation, related_name="members", on_delete="CASCADE", null=True)

    username = CharField(max_length=64, unique=True, null=True)
    password = TextField(null=True)

    @property
    def is_active(self):
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

class OrgAdmin(BaseModel):
    org = ForeignKeyField(Organisation, index=True, related_name="admins", on_delete="CASCADE")
    admin = ForeignKeyField(User, db_column="user_id", on_delete="CASCADE")

    class Meta:
        db_table = "org_admin"
        table_alias = "oa"
        primary_key = CompositeKey("admin", "org")

def create_tables():
    """
    Create all DB tables
    """
    try:
        db.connect()
    except OperationalError:
        pass
    models = (Organisation, User, OrgAdmin)
    db.create_tables(models)


def drop_talbes():
    """
    Drop all model tables
    """
    models = (m for m in globals().values() if isinstance(m, type) and issubclass(m, BaseModel))
    drop_model_tables(models, fail_silently=True, cascade=True)
