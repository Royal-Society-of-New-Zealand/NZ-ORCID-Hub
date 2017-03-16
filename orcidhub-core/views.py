# NB! Should be disabled in production
from pyinfo import info
from flask import render_template
from application import app, admin, db
from flask_admin.contrib.sqla import ModelView
from model import OrcidUser, Organisation, Researcher

@app.route('/pyinfo')
def pyinfo():
    return render_template('pyinfo.html', **info)


admin.add_view(ModelView(OrcidUser, db.session))
admin.add_view(ModelView(Organisation, db.session))
admin.add_view(ModelView(Researcher, db.session))
