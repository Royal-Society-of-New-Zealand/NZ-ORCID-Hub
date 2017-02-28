from application import db
from peewee import Model, CharField, DateTimeField, ForeignKeyField, \
    TextField, IntegerField, DateField, TimeField, BooleanField
from peewee import drop_model_tables

class BaseModel(Model):
    class Meta:
        database = db

class Researcher(BaseModel):
    rname = CharField(max_length=64, unique=True, verbose_name="Real Name")
    email = CharField(max_length=120, unique=True)
    orcid = CharField(max_length=120, unique=True, verbose_name="ORCID")
    auth_token = CharField(max_length=120, unique=True)

    def __repr__(self):
        return '<User %s>' % (self.rname)

    class Meta:
        table_alias = 'r'

def create_tables():
    """
    Create all DB tables
    """
    db.connect()
    models = (Researcher,)
    #models = (m for m in globals().values() if isinstance(m, type) and issubclass(m, Model))
    db.create_tables(models)


def drop_talbes():
    """
    Drop all model tables
    """
    models = (m for m in globals().values() if isinstance(m, type) and issubclass(m, Model))
    drop_model_tables(models, fail_silently=True)
