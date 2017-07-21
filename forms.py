# -*- coding: utf-8 -*-
"""Application forms."""

from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from pycountry import countries
from wtforms import (Field, SelectField, SelectMultipleField, StringField, validators)
from wtforms.fields.html5 import DateField, EmailField
from wtforms.validators import UUID, DataRequired, Email, Regexp
from wtforms.widgets import HTMLString, html_params

from config import DEFAULT_COUNTRY
from models import PartialDate as PD
from models import Organisation

# Order the countly list by the name and add a default (Null) value
country_choices = [(c.alpha_2, c.name) for c in countries]
country_choices.sort(key=lambda e: e[1])
country_choices.insert(0, ("", "Country"))


class PartialDate:
    """Widget for a partical date with 3 selectors (year, month, day)."""

    __current_year = date.today().year

    def __call__(self, field, **kwargs):
        """Render widget."""
        kwargs.setdefault('id', field.id)
        html = ["<!-- data: %r -->" % (field.data, ), '<div %s>' % html_params(**kwargs)]
        html.extend(self.render_select("year", field))
        html.extend(self.render_select("month", field))
        html.extend(self.render_select("day", field))
        html.append("</div>")
        return HTMLString(''.join(html))

    @classmethod
    def render_select(cls, part, field):
        """Render select for a specific part of date."""
        yield "<select %s>" % html_params(name=field.name + ":" + part)
        try:
            current_value = int(getattr(field.data, part))
        except:
            current_value = None
        # TODO: localization
        yield "<option %s>%s</option>" % (html_params(value="", selected=(current_value is None)),
                                          part.capitalize())
        option_format = "<option %s>%04d</option>" if part == "year" else "<option %s>%02d</option>"
        for v in range(cls.__current_year, 1912, -1) if part == "year" else range(
                1, 13 if part == "month" else 32):
            yield option_format % (html_params(value=v, selected=(v == current_value)), v)
        yield "</select>"


class PartialDateField(Field):
    """Partial date field."""

    widget = PartialDate()

    def process(self, formdata, data=None):
        """Process incoming data, calling process_data."""

        self.process_errors = []
        if data is None:
            data = self.default or PD()

        # self.object_data = data
        self.data = data

        if formdata is not None:
            new_data = {}
            for f in ("year", "month", "day", ):
                try:
                    if (self.name + ":" + f) in formdata:
                        raw_val = formdata.get(self.name + ":" + f)
                        value = int(raw_val) if raw_val else None
                    else:
                        value = getattr(self.data, f)
                    new_data[f] = value
                except ValueError as e:
                    new_data[f] = None
                    self.process_errors.append(e.args[0])
            self.data = PD(**new_data)
        try:
            for filter in self.filters:
                self.data = filter(self.data)
        except ValueError as e:
            self.process_errors.append(e.args[0])


class BitmapMultipleValueField(SelectMultipleField):
    """
    No different from a normal multi select field, except this one can take (and
    validate) multiple choices and value (by defualt) can be a bitmap of
    selected choices (the choice value should be an integer).
    """
    bitmap_value = True

    def process_data(self, value):
        try:
            if self.bitmap_value:
                self.data = [self.coerce(v) for (v, _) in self.choices if v & value]
            else:
                self.data = [self.coerce(v) for v in value]
        except (ValueError, TypeError):
            self.data = None

    def process_formdata(self, valuelist):
        try:
            if self.bitmap_value:
                self.data = sum(int(self.coerce(x)) for x in valuelist)
            else:
                self.data = [self.coerce(x) for x in valuelist]
        except ValueError:
            raise ValueError(
                self.gettext('Invalid choice(s): one or more data inputs could not be coerced'))

    def pre_validate(self, form):
        if self.data and not self.bitmap_value:
            values = list(c[0] for c in self.choices)
            for d in self.data:
                if d not in values:
                    raise ValueError(
                        self.gettext("'%(value)s' is not a valid choice for this field") % dict(
                            value=d))


class RecordForm(FlaskForm):
    """User/researcher employment detail form."""

    name = StringField("Institution/employer", [validators.required()])
    city = StringField("City", [validators.required()])
    state = StringField("State/region", filters=[lambda x: x or None])
    country = SelectField("Country", [validators.required()], choices=country_choices)
    department = StringField("Department", filters=[lambda x: x or None])
    role = StringField("Role/title", filters=[lambda x: x or None])
    start_date = PartialDateField("Start date")
    end_date = PartialDateField("End date (leave blank if current)")

    @classmethod
    def create_form(cls, *args, form_type=None, **kwargs):
        form = cls(*args, **kwargs)
        if form_type == "EDU":
            print(dir(form.name))
            form.name.name = "Institution"
            form.name.label.text = "Institution"
        return form


class FileUploadForm(FlaskForm):
    """Organisation info pre-loading form."""

    org_info = FileField(validators=[FileRequired(), FileAllowed(["csv"], 'CSV files only!')])


class OnboardingTokenForm(FlaskForm):
    """Form for requesting missing onboarding token."""

    token = StringField("Token", [validators.required()])


class OrgRegistrationForm(FlaskForm):
    orgName = StringField('Organisation Name: ', validators=[DataRequired()])
    orgEmailid = EmailField('Organisation EmailId: ', validators=[DataRequired(), Email()])


class OrgConfirmationForm(FlaskForm):
    orgName = StringField('Organisation Name: ', validators=[DataRequired()])
    orgEmailid = EmailField('Organisation EmailId: ', validators=[DataRequired(), Email()])
    orgOricdClientId = StringField(
        'Organisation Orcid Client Id: ',
        validators=[
            DataRequired(),
            Regexp(r"^\S+$", message="The value shouldn't contain any spaces"),
            Regexp(
                r"^APP-[A-Z0-9]+$",
                message=("The Cient ID should match patter "
                         "'APP-(sequence of digits or uppercase characters), "
                         "for example, 'APP-FDFN3F52J3M4L34S'.")),
        ])
    orgOrcidClientSecret = StringField(
        'Organisation Orcid Client Secret: ',
        validators=[
            DataRequired(), Regexp(r"^\S+$", message="The value shouldn't contain any spaces"),
            UUID(message="The secret should be a valid UUID")
        ])
    country = SelectField(
        "Country", [validators.required()], choices=country_choices, default=DEFAULT_COUNTRY)
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


class DateRangeForm(FlaskForm):
    from_date = DateField('DatePicker', format='%Y-%m-%d')
    to_date = DateField('DatePicker', format='%Y-%m-%d')


class SelectOrganisation(FlaskForm):
    orgNames = SelectField(
        "orgNames",
        [validators.required()], )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orgNames.choices = Organisation.select(
            Organisation.id, Organisation.name).order_by(Organisation.name).tuples()
