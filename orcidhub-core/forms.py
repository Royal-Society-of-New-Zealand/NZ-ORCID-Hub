from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, validators
from pycountry import countries


class EmploymentForm(FlaskForm):
    employer = StringField("Institution/employer", [validators.required()])
    city = StringField("City", [validators.required()])
    state = StringField("State/region", [validators.required()])
    country = SelectField("Country", [validators.required()], choices=((c.alpha_2, c.name) for c in countries))
    department = StringField("Department")
    role = StringField("Role/title")
    start_date = DateField("Start date", format="%Y-%m-%d")
    end_date = DateField("End date (leave blank if current)", format="%Y-%m-%d")

