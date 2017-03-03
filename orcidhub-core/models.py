from peewee import Model, CharField
from peewee import drop_model_tables, OperationalError
from application import db

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

    class Meta:
        table_alias = 'r'


def create_tables():
    """
    Create all DB tables
    """
    try:
        db.connect()
    except OperationalError:
        pass
    models = (Researcher,)
    db.create_tables(models)


def drop_talbes():
    """
    Drop all model tables
    """
    models = (m for m in globals().values() if isinstance(m, type) and issubclass(m, BaseModel))
    drop_model_tables(models, fail_silently=True)
