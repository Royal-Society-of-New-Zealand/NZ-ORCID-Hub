from peewee import Model, CharField, BooleanField, SmallIntegerField, ForeignKeyField
from peewee import drop_model_tables, OperationalError
from application import db
from enum import IntFlag
from flask_login import UserMixin

class UserRole(IntFlag):
    """
    Enum used to represent user role
    """
    ANY = 0  # ANY
    SUPERUSER = 1  # SuperUser
    ADMIN = 2  # Admin
    RESEARCHER = 4  # Researcher

class BaseModel(Model):

    class Meta:
        database = db

class Researcher(BaseModel):

    rname = CharField(max_length=64, unique=True, verbose_name="Real Name")
    email = CharField(max_length=120, unique=True)
    orcid = CharField(max_length=120, unique=True, verbose_name="ORCID")
    auth_token = CharField(max_length=120, unique=True)
    edu_person_shared_token = CharField(max_length=120, unique=True, verbose_name="EDU Person Shared Token")

    def __repr__(self):
        return '<User %s>' % (self.rname)

class Organisation(BaseModel):

    name = CharField(max_length=100, unique=True)
    email = CharField(max_length=80, unique=True)
    tuakiri_name = CharField(max_length=80, unique=True)
    orcid_client_id = CharField(max_length=80, unique=True)
    orcid_secret = CharField(max_length=80, unique=True)
    confirmed = BooleanField(default=False)

class OrcidUser(BaseModel, UserMixin):

    rname = CharField(max_length=64, unique=True, verbose_name="Real Name")
    email = CharField(max_length=120, unique=True)
    orcid = CharField(max_length=120, unique=True, verbose_name="ORCID")
    auth_token = CharField(max_length=120, unique=True)
    edu_person_shared_token = CharField(max_length=120, unique=True, verbose_name="EDU Person Shared Token")
    confirmed = BooleanField(default=False)
    role = SmallIntegerField(default=0)
    organisation = ForeignKeyField(Organisation, related_name="members", on_delete="CASCADE")

    @property
    def is_active(self):
        return self.confirmed

    @is_active.setter
    def is_activate(self, value):
        self.confirmed = value

    @property
    def user_role(self):
        return UserRole(self.role)

    @user_role.setter
    def user_role(self, value):
        assert type(value) == UserRole
        self.role = value.value


def create_tables():
    """
    Create all DB tables
    """
    try:
        db.connect()
    except OperationalError:
        pass
    models = (Researcher, Organisation, OrcidUser)
    db.create_tables(models)


def drop_talbes():
    """
    Drop all model tables
    """
    models = (m for m in globals().values() if isinstance(m, type) and issubclass(m, BaseModel))
    drop_model_tables(models, fail_silently=True)
