from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.fields.html5 import EmailField


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
