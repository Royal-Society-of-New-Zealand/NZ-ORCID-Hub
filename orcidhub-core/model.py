from application import db


class Researcher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    orcidid = db.Column(db.String(120), index=True, unique=True)
    auth_token = db.Column(db.String(120), index=True, unique=True)

    def __repr__(self):
        return '<User %r>' % (self.rname)
