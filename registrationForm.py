from flask_wtf import FlaskForm
from pycountry import countries
from wtforms import StringField, validators
from wtforms.fields.core import SelectField
from wtforms.fields.html5 import DateField, EmailField
from wtforms.validators import DataRequired, Email

# Order the countly list by the name and add a default (Null) value
country_choices = [(c.alpha_2, c.name) for c in countries]
country_choices.sort(key=lambda e: e[1])
country_choices.insert(0, ("", "Country"))


class OrgRegistrationForm(FlaskForm):
    orgName = StringField('Organisation Name: ', validators=[DataRequired()])
    orgEmailid = EmailField('Organisation EmailId: ', validators=[DataRequired(), Email()])


class OrgConfirmationForm(FlaskForm):
    orgName = StringField('Organisation Name: ', validators=[DataRequired()])
    orgEmailid = EmailField('Organisation EmailId: ', validators=[DataRequired(), Email()])
    orgOricdClientId = StringField('Organisation Orcid Client Id: ', validators=[DataRequired()])
    orgOrcidClientSecret = StringField(
        'Organisation Orcid Client Secret: ', validators=[DataRequired()])
    country = SelectField("Country", [validators.required()], choices=country_choices, default="NZ")
    city = StringField("City", [validators.required()])
    disambiguation_org_id = StringField("Disambiguation ORG Id", [validators.required()])
    disambiguation_org_source = StringField("Disambiguation ORG Source", [validators.required()])


class EmploymentDetailsForm(FlaskForm):
    institution = StringField('Institution/Organisation: ', validators=[DataRequired()])
    city = StringField('City: ', validators=[DataRequired()])
    state = StringField('State/Region: ', validators=[DataRequired()])
    country = SelectField('Country: ', choices=[('NZ', 'New Zealand'), ('Au', 'Australia')])
    department = StringField('Department: ', validators=[DataRequired()])
    role = StringField('Role: ', validators=[DataRequired()])
    title = StringField('Title: ', validators=[DataRequired()])
    start_date = DateField('Start Date: ', format='%m/%d/%Y', validators=[DataRequired])
    end_date = DateField('End Date: ', format='%m/%d/%Y', validators=[DataRequired])
