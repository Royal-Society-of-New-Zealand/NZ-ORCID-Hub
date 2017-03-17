from application import db
import enum
from flask_login import UserMixin


# Enum used to represent user role
class Role(enum.Enum):
    ADMIN = "Admin"
    SUPERUSER = "SuperUser"
    RESEARCHER = "Researcher"
    ANY = "ANY"


class Researcher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    orcidid = db.Column(db.String(120), index=True, unique=True)
    auth_token = db.Column(db.String(120), index=True, unique=True)
    auedupersonsharedtoken = db.Column(db.String(120), index=True, unique=True)

    def __repr__(self):
        return '<User %r>' % (self.rname)


class Organisation(db.Model):
    __tablename__ = 'organisation'
    org_name = db.Column(db.String(100), index=True)
    emailid = db.Column(db.String(80), index=True, primary_key=True, unique=True)
    tuakiriname = db.Column(db.String(80), index=True, unique=True)
    orcid_client_id = db.Column(db.String(80), index=True, unique=True)
    orcid_secret = db.Column(db.String(80), index=True, unique=True)
    members = db.relationship('OrcidUser', backref="organisation", cascade="all, delete-orphan", lazy='dynamic')
    confirmed = db.Column(db.Boolean, default=False, unique=False)


class OrcidUser(db.Model, UserMixin):
    __tablename__ = 'orciduser'
    # id = db.Column(db.Integer, primary_key=True)
    rname = db.Column(db.String(64), index=True, unique=False)
    email = db.Column(db.String(120), index=True, unique=True, primary_key=True)
    orcidid = db.Column(db.String(120), index=True, unique=True)
    auth_token = db.Column(db.String(120), index=True, unique=True)
    auedupersonsharedtoken = db.Column(db.String(120), index=True, unique=True)
    # TODO: Seems some bug in flask SQLAlchemy
    is_active = db.Column(db.Boolean, default=True, unique=False)
    confirmed = db.Column(db.Boolean, default=False, unique=False)
    urole = db.Column(db.Enum(Role))
    orgid = db.Column(db.String(80), db.ForeignKey('organisation.emailid'))

    # def __init__(self,username,pwd_hash,email,is_active,urole,auedupersonsharedtoken):
    #    self.rname = username
    #    self.pwd_hash = pwd_hash
    #    self.email = email
    #    self.is_active = is_active
    #    self.urole = urole

    def get_id(self):
        return self.email

    def is_active(self):
        return self.confirmed  # self.is_active  TODO: Seems some bug in flask login

    def activate_user(self):
        self.confirmed = True

    def get_username(self):
        return self.rname

    def get_urole(self):
        return self.urole
