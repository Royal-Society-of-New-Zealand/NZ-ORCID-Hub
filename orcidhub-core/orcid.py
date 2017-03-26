# -*- coding: utf-8 -*-

"""Orcid view models for using with Flask-Admin CRUD funcions."""

from flask_admin.model import BaseModelView
from models import Role

# TODO: expand ...

class EmploymentModelView(BaseModelView):
    """Employemnt data view."""

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role(Role.ADMIN|Role.SUPERUSER):
            return True

        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

    def get_pk_value(self, model):
        return


