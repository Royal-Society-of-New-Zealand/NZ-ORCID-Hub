# -*- coding: utf-8 -*-
"""Application forms."""

from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, Field, SelectField, SelectMultipleField, StringField,
                     SubmitField, TextField, TextAreaField, validators)
from wtforms.fields.html5 import DateField, EmailField, IntegerField
from wtforms.validators import (UUID, DataRequired, email, Regexp, StopValidation, ValidationError, optional, url)
from wtforms.widgets import HTMLString, TextArea, html_params
from wtfpeewee.orm import model_form

from . import app, models

DEFAULT_COUNTRY = app.config["DEFAULT_COUNTRY"]
EMPTY_CHOICES = [("", "")]


def validate_orcid_id_field(form, field):
    """Validate ORCID iD."""
    if not field.data:
        return
    try:
        models.validate_orcid_id(field.data)
    except ValueError as ex:
        raise ValidationError(str(ex))


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
        # If user didn't specifiy the date then the year range will start from current year + 5 years
        range_value = cls.__current_year + 5
        try:
            current_value = int(getattr(field.data, part))
            range_value = current_value + 5
        except Exception:
            current_value = None
        # TODO: localization
        yield "<option %s>%s</option>" % (html_params(value="", selected=(current_value is None)),
                                          part.capitalize())
        option_format = "<option %s>%04d</option>" if part == "year" else "<option %s>%02d</option>"
        for v in range(range_value, 1912, -1) if part == "year" else range(
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
            data = self.default or models.PartialDate()

        # self.object_data = data
        self.data = data

        if formdata is not None:
            new_data = {}
            for f in (
                    "year",
                    "month",
                    "day",
            ):
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

            self.data = models.PartialDate(**new_data)
        try:
            for f in self.filters:
                self.data = f(self.data)
        except ValueError as e:
            self.process_errors.append(e.args[0])

    def pre_validate(self, form):
        """Validate entered fuzzy/partial date value."""
        if self.data.day and not (self.data.month and self.data.year):
            raise StopValidation(f"Invalid date: {self.data}. Missing year and/or month value.")
        y, m, d = self.data.year, self.data.month, self.data.day
        if m is not None:
            if y is None:
                raise StopValidation(f"Invalid date: {self.data}. Missing year value.")
            if m < 1 or m > 12:
                raise StopValidation(f"Invalid month: {m}")
            if d is not None:
                if d < 1 or d > 31:
                    raise StopValidation(f"Invalid day: {d}.")
                elif m % 2 == (0 if m < 8 else 1) and d > 30:
                    raise StopValidation(f"Invalid day: {d}. It should be less than 31.")
                elif m == 2:
                    if d > 29:
                        raise StopValidation(f"Invalid day: {d}. February has at most 29 days.")
                    elif y % 4 != 0 and d > 28:
                        raise StopValidation(
                            f"Invalid day: {d}. It should be less than 29 (Leap Year).")


class CountrySelectField(SelectField):
    """Country dropdown widget."""

    def __init__(self, *args, **kwargs):
        """Set up the value list."""
        if len(args) == 0 and "label" not in kwargs:
            kwargs["label"] = "Country"
        super().__init__(*args, choices=EMPTY_CHOICES + models.country_choices, **kwargs)


class LanguageSelectField(SelectField):
    """Languages dropdown widget."""

    def __init__(self, *args, **kwargs):
        """Set up the value list."""
        if len(args) == 0 and "label" not in kwargs:
            kwargs["label"] = "Language"
        super().__init__(*args, choices=EMPTY_CHOICES + models.language_choices, **kwargs)


class CurrencySelectField(SelectField):
    """currencies dropdown widget."""

    def __init__(self, *args, **kwargs):
        """Set up the value list."""
        if len(args) == 0 and "label" not in kwargs:
            kwargs["label"] = "Currency"
        super().__init__(*args, choices=EMPTY_CHOICES + models.currency_choices, **kwargs)


class BitmapMultipleValueField(SelectMultipleField):
    """Multiple value selection widget.

    No different from a normal multi select field, except this one can take (and
    validate) multiple choices and value (by defualt) can be a bitmap of
    selected choices (the choice value should be an integer).
    """

    is_bitmap_value = True

    def iter_choices(self):
        """Iterate through the list of choces."""
        if self.is_bitmap_value and isinstance(self.data, int):
            for value, label in self.choices:
                yield (value, label, bool(self.data & value))
        else:
            yield from super().iter_choices()

    def process_data(self, value):
        """Map selected value representation to the a list to internal domain value."""
        try:
            if self.is_bitmap_value:
                self.data = [self.coerce(v) for (v, _) in self.choices if v & value]
            else:
                self.data = [self.coerce(v) for v in value]
        except (ValueError, TypeError):
            self.data = None

    def process_formdata(self, valuelist):
        """Map submitted value to the domain value."""
        try:
            if self.is_bitmap_value:
                self.data = sum(int(self.coerce(x)) for x in valuelist)
            else:
                self.data = [self.coerce(x) for x in valuelist]
        except ValueError:
            raise ValueError(
                self.gettext('Invalid choice(s): one or more data inputs could not be coerced'))

    def pre_validate(self, form):
        """Pre-validate if it's not bit-map."""
        if self.data and not self.is_bitmap_value:
            values = list(c[0] for c in self.choices)
            for d in self.data:
                if d not in values:
                    raise ValueError(
                        self.gettext("'%(value)s' is not a valid choice for this field") %
                        dict(value=d))


class AppForm(FlaskForm):
    """Application Flask-WTForm extension."""

    @models.lazy_property
    def enctype(self):
        """Return form's encoding type based on the fields.

        If there is at least one FileField the encoding type will be set to "multipart/form-data".
        """
        return "multipart/form-data" if any(f.type == "FileField" for f in self) else ''


class FundingForm(FlaskForm):
    """User/researcher funding detail form."""

    type_choices = [(v, v.replace('_', ' ').title()) for v in [''] + models.FUNDING_TYPES]

    funding_title = StringField("Funding Title", [validators.required()])
    funding_translated_title = StringField("Funding Translated Title")
    translated_title_language = LanguageSelectField("Language")
    funding_type = SelectField(choices=type_choices, description="Funding Type", validators=[validators.required()])
    funding_subtype = StringField("Funding Subtype")
    funding_description = TextAreaField("Funding Description")
    total_funding_amount = StringField("Total Funding Amount")
    total_funding_amount_currency = CurrencySelectField("Currency")
    org_name = StringField("Institution/employer", [validators.required()])
    city = StringField("City", [validators.required()])
    state = StringField("State/region", filters=[lambda x: x or None])
    country = CountrySelectField("Country", [validators.required()])
    start_date = PartialDateField("Start date")
    end_date = PartialDateField("End date (leave blank if current)")
    disambiguated_id = StringField("Disambiguated Organisation ID")
    disambiguation_source = SelectField(
        "Disambiguation Source",
        validators=[optional()],
        choices=EMPTY_CHOICES + models.disambiguation_source_choices)


class PeerReviewForm(FlaskForm):
    """User/researcher Peer review detail form."""

    reviewer_role_choices = [(v, v.replace('_', ' ').title())
                             for v in [''] + models.REVIEWER_ROLES]
    subject_type_choices = [(v, v.replace('_', ' ').title()) for v in [''] + models.SUBJECT_TYPES]

    org_name = StringField("Institution", [validators.required()])
    disambiguated_id = StringField("Disambiguated Organisation ID")
    disambiguation_source = SelectField(
        "Disambiguation Source",
        validators=[optional()],
        choices=EMPTY_CHOICES + models.disambiguation_source_choices)
    city = StringField("City", [validators.required()])
    state = StringField("State/region", filters=[lambda x: x or None])
    country = CountrySelectField("Country", [validators.required()])
    reviewer_role = SelectField(
        choices=reviewer_role_choices,
        description="Reviewer Role",
        validators=[validators.required()])
    review_url = StringField("Review Url")
    review_type = SelectField(
        choices=EMPTY_CHOICES + models.review_type_choices,
        description="Review Type",
        validators=[validators.required()])
    review_group_id = StringField("Peer Review Group Id", [validators.required()])
    subject_external_identifier_type = StringField("Subject External Identifier Type")
    subject_external_identifier_value = StringField("Subject External Identifier Value")
    subject_external_identifier_url = StringField("Subject External Identifier Url")
    subject_external_identifier_relationship = SelectField(
        choices=EMPTY_CHOICES + models.relationship_choices,
        description="Subject External Id Relationship")
    subject_container_name = StringField("Subject Container Name")
    subject_type = SelectField(choices=subject_type_choices, description="Subject Type")
    subject_title = StringField("Subject Title")
    subject_subtitle = StringField("Subject Subtitle")
    subject_translated_title = StringField("Subject Translated Title")
    subject_translated_title_language_code = LanguageSelectField("Language")
    subject_url = StringField("Subject Url")
    review_completion_date = PartialDateField(
        "Review Completion date", validators=[validators.required()])


class WorkForm(FlaskForm):
    """User/researcher Work detail form."""

    work_type = SelectField(
        choices=EMPTY_CHOICES + models.work_type_choices,
        description="Work Type",
        validators=[validators.required()])
    title = StringField("Title", [validators.required()])
    subtitle = StringField("Subtitle")
    translated_title = StringField("Translated Title")
    translated_title_language_code = LanguageSelectField("Language")
    journal_title = StringField("Work Type Title")
    short_description = TextAreaField(description="Short Description")
    citation_type = SelectField(
        choices=EMPTY_CHOICES + models.citation_type_choices, description="Citation Type")
    citation = StringField("Citation Value")
    publication_date = PartialDateField("Publication date")
    url = StringField("Url")
    language_code = LanguageSelectField("Language used in this form")
    country = CountrySelectField("Country of publication")


class CommonFieldsForm(FlaskForm):
    """User/researcher Url and Other Name Common form."""

    visibility_choices = [(v, v.replace('_', ' ').title()) for v in models.VISIBILITIES]
    display_index = StringField("Display Index")
    visibility = SelectField(choices=visibility_choices, description="Visibility")


class ResearcherUrlForm(CommonFieldsForm):
    """User/researcher Url detail form."""

    name = StringField("Url Name", [validators.required()])
    value = StringField("Url Value", [validators.required()])


class OtherNameKeywordForm(CommonFieldsForm):
    """User/researcher other name detail form."""

    content = StringField("Content", [validators.required()])


class AddressForm(CommonFieldsForm):
    """User/researcher address detail form."""

    country = CountrySelectField("Country", [validators.required()])


class ExternalIdentifierForm(CommonFieldsForm):
    """User/researcher Other IDs detail form."""

    type = SelectField(choices=EMPTY_CHOICES + models.external_id_type_choices, validators=[validators.required()],
                       description="External Identifier Type")
    value = StringField("External Identifier Value", [validators.required()])
    url = StringField("External Identifier Url", [validators.required()])
    relationship = SelectField(choices=models.relationship_choices, default="SELF",
                               description="External Id Relationship")


class RecordForm(CommonFieldsForm):
    """User/researcher employment detail form."""

    org_name = StringField("Institution/employer", [validators.required()])
    city = StringField("City", [validators.required()])
    state = StringField("State/region", filters=[lambda x: x or None])
    country = CountrySelectField("Country", [validators.required()])
    department = StringField("Department", filters=[lambda x: x or None])
    role = StringField("Role/title", filters=[lambda x: x or None])
    start_date = PartialDateField("Start date")
    end_date = PartialDateField("End date (leave blank if current)")
    disambiguated_id = StringField("Disambiguated Organisation ID")
    disambiguation_source = SelectField(
        "Disambiguation Source",
        validators=[optional()],
        choices=EMPTY_CHOICES + models.disambiguation_source_choices)
    url = StringField("Url", filters=[lambda x: x or None])

    def __init__(self, *args, form_type=None, **kwargs):
        """Create form."""
        super().__init__(*args, **kwargs)
        if form_type == "EDU":
            self.org_name.label = "Institution"
            self.role.label = "Course/Degree"


class GroupIdForm(FlaskForm):
    """GroupID record form."""

    group_id_name = StringField("Group ID Name", [validators.required()])
    page_size = StringField("Page Size")
    page = StringField("Page")
    search = SubmitField("Search", render_kw={"class": "btn btn-primary"})


class FileUploadForm(AppForm):
    """Generic data (by default CSV or TSV) load form."""

    file_ = FileField()
    upload = SubmitField("Upload", render_kw={"class": "btn btn-primary"})

    def __init__(self, *args, optional=None, extensions=None, **kwargs):
        """Customize the form."""
        super().__init__(*args, **kwargs)
        if not optional:
            self.file_.validators.append(FileRequired())
            self.file_.flags.required = True
        if extensions is None:
            extensions = ["csv", "tsv"]
        accept_attr = ", ".join('.' + e for e in extensions)
        self.file_.render_kw = {
            "accept": accept_attr,
        }
        extensions_ = [e.upper() for e in extensions]
        self.file_.validators.append(
            FileAllowed(
                extensions, " or ".join(
                    (", ".join(extensions_[:-1]), extensions_[-1])) + " file(-s) only"))


class TestDataForm(FileUploadForm):
    """Load testing data upload and/or generation form."""

    org_count = IntegerField(
        label="Organisation Count",
        default=100,
        render_kw=dict(style="width: 10%; max-width: 10em;"))
    use_known_orgs = BooleanField(label="Use Existing Confirmed Organisations", default=False)
    user_count = IntegerField(
        label="Organisation Count",
        default=400,
        render_kw=dict(style="width: 10%; max-width: 10em;"))
    upload = SubmitField(
        "Upload or Generate",
        render_kw={
            "class": "btn btn-primary",
            "data-toggle": "tooltip",
            "title": "Sign the uploaded data entries or generate them from the scratch"
        })


class LogoForm(FlaskForm):
    """Organisation Logo image upload form."""

    logo_file = FileField(validators=[
        FileRequired(),
        FileAllowed(["gif", "png", "jpg"], 'Only image files allowed!')
    ])
    upload = SubmitField("Upload", render_kw={"class": "btn btn-primary"})
    reset = SubmitField("Reset", render_kw={"class": "btn btn-danger"})
    cancel = SubmitField("Cancel", render_kw={"class": "btn btn-invisible"})


class EmailTemplateForm(FlaskForm):
    """Email template form."""

    email_template = TextField(
        widget=TextArea(), render_kw={
            "style": "min-width: 800px;min-height: 550px;"
        })
    email_template_enabled = BooleanField(default=False)
    prefill = SubmitField("Pre-fill", render_kw={"class": "btn btn-default"})
    reset = SubmitField("Reset", render_kw={"class": "btn btn-danger"})
    send = SubmitField("Send", render_kw={"class": "btn btn-primary"})
    save = SubmitField("Save", render_kw={"class": "btn btn-success"})
    cancel = SubmitField("Cancel", render_kw={"class": "btn btn-invisible"})


class OnboardingTokenForm(FlaskForm):
    """Form for requesting missing onboarding token."""

    token = StringField("Token", [validators.required()])


class RequiredIf(DataRequired):
    """Condition validator.

    A validator which makes a field required if
    another field is set and has a truthy value.
    """

    field_flags = ('requiredif',)

    def __init__(self, other_field_name, *args, **kwargs):
        """Link the condtion field to the validator."""
        self.other_field_name = other_field_name
        super().__init__(*args, **kwargs)

    def __call__(self, form, field):
        """Validate conditionally if the linked field has a value."""
        other_field = form[self.other_field_name]
        if other_field is None:
            raise Exception(f'no field named "{self.other_field_name}" in form')
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)


class OrgRegistrationForm(FlaskForm):
    """Organisation registration/invitation form."""

    org_name = StringField('Organisation Name', validators=[DataRequired()])
    org_email = EmailField('Organisation Email', validators=[DataRequired(), email()])
    tech_contact = BooleanField("Technical Contact", default=False)
    via_orcid = BooleanField("ORCID Authentication", default=False)
    first_name = StringField(
        "First Name", validators=[
            RequiredIf("via_orcid"),
        ])
    last_name = StringField(
        "Last Name", validators=[
            RequiredIf("via_orcid"),
        ])
    orcid_id = StringField("ORCID iD", [
        validate_orcid_id_field,
    ])
    city = StringField(
        "City", validators=[
            RequiredIf("via_orcid"),
        ])
    state = StringField("State/Region")
    country = CountrySelectField(
        "Country", default=DEFAULT_COUNTRY, validators=[
            RequiredIf("via_orcid"),
        ])
    course_or_role = StringField("Course or Job title")
    disambiguated_id = StringField("Disambiguated Id")
    disambiguation_source = SelectField(
        "Disambiguation Source",
        validators=[optional()],
        choices=EMPTY_CHOICES + models.disambiguation_source_choices)


class OrgConfirmationForm(FlaskForm):
    """Registered organisation confirmation form."""

    name = StringField('Organisation Name', validators=[DataRequired()])
    email = EmailField('Organisation EmailId', validators=[DataRequired(), email()])
    show_api_credentials = BooleanField("Show API Credentials", default=False)
    orcid_client_id = StringField(
        "Organisation Orcid Client Id: ",
        validators=[
            DataRequired(),
            Regexp(r"^\S+$", message="The value shouldn't contain any spaces"),
            Regexp(
                r"^APP-[A-Z0-9]+$",
                message=("The Cient ID should match patter "
                         "'APP-(sequence of digits or uppercase characters), "
                         "for example, 'APP-FDFN3F52J3M4L34S'.")),
        ])
    orcid_secret = StringField(
        'Organisation Orcid Client Secret: ',
        validators=[
            DataRequired(),
            Regexp(r"^\S+$", message="The value shouldn't contain any spaces"),
            UUID(message="The secret should be a valid UUID")
        ])
    country = CountrySelectField("Country", [validators.required()], default=DEFAULT_COUNTRY)
    city = StringField("City", [validators.required()])
    disambiguated_id = StringField("Disambiguated Id", [validators.required()])
    disambiguation_source = SelectField(
        "Disambiguation Source",
        validators=[validators.required()],
        choices=EMPTY_CHOICES + models.disambiguation_source_choices)


class UserInvitationForm(FlaskForm):
    """Single user invitation form."""

    first_name = StringField("First Name", [validators.required()])
    last_name = StringField("Last Name", [validators.required()])
    email_address = EmailField("Email Address", [validators.required(), email()])
    orcid_id = StringField("ORCID iD", [
        validate_orcid_id_field,
    ])
    department = StringField("Campus/Department")
    organisation = StringField("Organisation Name")
    city = StringField("City", [validators.required()])
    state = StringField("State/Region")
    country = CountrySelectField("Country", [validators.required()], default=DEFAULT_COUNTRY)
    course_or_role = StringField("Course or Job title")
    start_date = PartialDateField("Start date")
    end_date = PartialDateField("End date (leave blank if current)")
    is_student = BooleanField("Student")
    is_employee = BooleanField("Staff")
    disambiguated_id = StringField("Disambiguated Id")
    disambiguation_source = SelectField(
        "Disambiguation Source",
        validators=[optional()],
        choices=EMPTY_CHOICES + models.disambiguation_source_choices)
    resend = BooleanField("Resend")


class DateRangeForm(FlaskForm):
    """Simple date range selection form with ISO dates."""

    from_date = DateField('DatePicker', format='%Y-%m-%d')
    to_date = DateField('DatePicker', format='%Y-%m-%d')


class ApplicationFromBase(FlaskForm):
    """User/client application registration management form."""

    name = StringField("Application name", [validators.required()])
    homepage_url = StringField("Homepage URL")
    description = TextField("Application Description")
    callback_urls = TextField("Authorization callback URLs")


class ApplicationFrom(ApplicationFromBase):
    """Application client registration form."""

    register = SubmitField("Register", render_kw={"class": "btn btn-primary mr-2"})
    cancel = SubmitField("Cancel", render_kw={"class": "btn btn-invisible"})


class CredentialForm(ApplicationFromBase):
    """User/client application credential registration management form."""

    client_id = StringField("Client ID", render_kw={"readonly": True})
    client_secret = StringField("Client Secret", render_kw={"readonly": True})
    revoke = SubmitField("Revoke all user tokens", render_kw={"class": "btn btn-danger"})
    reset = SubmitField("Reset client secret", render_kw={"class": "btn btn-danger"})
    update_app = SubmitField("Update application", render_kw={"class": "btn btn-primary mr-2"})
    delete = SubmitField("Delete application", render_kw={"class": "btn btn-danger"})


class WebhookForm(
        model_form(
            models.Organisation,
            base_class=FlaskForm,
            only=[
                "webhook_enabled",
                "webhook_url",
                "email_notifications_enabled",
                "notification_email",
            ],
            field_args=dict(
                notification_email=dict(
                    render_kw={
                        "data-toggle":
                        "tooltip",
                        "title":
                        "Alternative notification e-mail address (defaut: the technical constact e-mail address)"
                    },
                    validators=[optional(), email()]),
                webhook_url=dict(validators=[optional(), url()])))):
    """Webhoook form."""

    save_webhook = SubmitField(
        "Save",
        render_kw={
            "class": "btn btn-success",
            "data-toggle": "tooltip",
            "title": "Save Organisation webhook"
        })


class ProfileSyncForm(FlaskForm):
    """Profile sync form."""

    start = SubmitField(
        "Start",
        render_kw={
            "class": "btn btn-primary mr-2",
            "data-toggle": "tooltip",
            "title": "Start profile synchronization"
        })
    restart = SubmitField(
        "Restart",
        render_kw={
            "class": "btn btn-secondary mr-2",
            "data-toggle": "tooltip",
            "title": "Re-start profile synchronization"
        })
    close = SubmitField(
        "Close",
        render_kw={
            "class": "btn btn-invisible",
            "data-toggle": "tooltip",
            "title": "Cancel profile synchronization"
        })
