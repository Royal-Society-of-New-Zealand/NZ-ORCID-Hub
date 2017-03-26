from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.fields.core import SelectField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.fields.html5 import EmailField, DateField


class OrgRegistrationForm(FlaskForm):
    orgName = StringField('Organisation Name: ', validators=[DataRequired()])
    orgEmailid = EmailField('Organisation EmailId: ',
                            validators=[DataRequired(), Email()])


class OrgConfirmationForm(FlaskForm):
    orgName = StringField('Organisation Name: ', validators=[DataRequired()])
    orgEmailid = EmailField('Organisation EmailId: ',
                            validators=[DataRequired(), Email()])
    orgOricdClientId = StringField('Organisation Orcid Client Id: ', validators=[DataRequired()])
    orgOrcidClientSecret = StringField('Organisation Orcid Client Secret: ',
                                       validators=[DataRequired()])


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
