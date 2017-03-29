# -*- coding: utf-8 -*-

"""Application forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, validators, Field
from wtforms.widgets import HTMLString, html_params
from pycountry import countries
from datetime import date
from models import PartialDate as PD

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
        html = ["<!-- data: %r -->" % (field.data,), '<div %s>' % html_params(name=field.name, **kwargs)]
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
        yield "<option %s>%s</option>" % (html_params(value="", selected=(current_value is None)), part.capitalize())
        option_format = "<option %s>%04d</option>" if part == "year" else "<option %s>%02d</option>"
        for v in range(cls.__current_year, 1912, -1) if part == "year" else range(1, 13 if part == "month" else 32):
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
            for f in ("year", "month", "day",):
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


class EmploymentForm(FlaskForm):
    """User/researcher employment detail form."""

    name = StringField("Institution/employer", [validators.required()])
    city = StringField("City", [validators.required()])
    state = StringField("State/region")
    country = SelectField("Country", [validators.required()], choices=country_choices)
    department = StringField("Department")
    role = StringField("Role/title")
    # TODO: Change to partial date (with dropdowns) widgets
    start_date = PartialDateField("Start date")
    end_date = PartialDateField("End date (leave blank if current)")
