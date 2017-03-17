# NB! Should be disabled in production
from pyinfo import info
from flask import render_template
from application import app, admin
from flask_admin.contrib.peewee import ModelView
from models import User, Organisation

@app.route('/pyinfo')
def pyinfo():
    return render_template('pyinfo.html', **info)


admin.add_view(ModelView(User))
admin.add_view(ModelView(Organisation))
