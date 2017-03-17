# NB! Should be disabled in production
from pyinfo import info
from flask import render_template, redirect, url_for, request
from application import app, admin
from flask_admin.contrib.peewee import ModelView
from models import User, Organisation, Role
from flask_login import login_required, current_user

@app.route('/pyinfo')
@login_required
def pyinfo():
    return render_template('pyinfo.html', **info)


class AppModelView(ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role(Role.SUPERUSER):
            return True

        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))


admin.add_view(AppModelView(User))
admin.add_view(AppModelView(Organisation))
