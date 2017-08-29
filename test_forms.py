# -*- coding: utf-8 -*-
"""Tests for forms and WTForms extensions."""

from unittest.mock import MagicMock

import pytest
from wtforms import Form

from forms import PartialDate, PartialDateField
from models import PartialDate as PD


def test_partial_date_widget():
    assert '<option selected value="1995">1995</option>' in PartialDate()(MagicMock(data=PD(1995)))

    field = MagicMock(label="LABEL", id="ID", data=PD(2017, 5, 13))
    field.name = "NAME"
    pd = PartialDate()(field)
    assert '<option selected value="2017">2017</option>' in pd
    assert '<option selected value="5">05</option>' in pd
    assert '<option selected value="13">13</option><option value="14">14</option>' in pd
    assert '"NAME:year"' in pd
    assert '"NAME:month"' in pd
    assert '"NAME:day"' in pd


@pytest.fixture
def test_form():
    class F(Form):
        pdf1 = PartialDateField("f1", default=PD(1995), id="test-id-1")
        pdf2 = PartialDateField("f2", default=PD(2017, 5, 13), id="test-id-2")
        pdf3 = PartialDateField("f3")

    return F


def test_partial_date_field_defaults(test_form):

    tf = test_form()
    assert tf.pdf1.data == PD(1995)
    assert tf.pdf2.data == PD(2017, 5, 13)
    assert tf.pdf1.label.text == "f1"


class DummyPostData(dict):
    def __init__(self, data):
        super().__init__()
        self.update(data)

    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_partial_date_field_with_data(test_form):

    tf = test_form(DummyPostData({"pdf1:year": "2000", "pdf1:month": "1", "pdf1:day": "31"}))
    pdf1 = tf.pdf1()

    assert '<option selected value="31">' in pdf1
    assert '<option value="2001">2001</option><option selected value="2000">2000</option>' in pdf1
    assert '<option value="">Month</option><option selected value="1">01</option><option value="2">' in pdf1


def test_partial_date_field_errors(test_form):

    tf = test_form(
        DummyPostData({
            "pdf1:year": "ERROR",
            "pdf1:month": "ERROR",
            "pdf1:day": "ERROR"
        }))
    assert len(tf.pdf1.process_errors) > 0


def test_partial_date_field_with_filter(test_form):

    test_form.pdf = PartialDateField(
        "f", filters=[lambda pd: PD(pd.year + 1, pd.month + 1, pd.day + 1)])

    tf = test_form(DummyPostData({"pdf:year": "2012", "pdf:month": "4", "pdf:day": "12"}))
    pdf = tf.pdf()

    assert '<option selected value="13">' in pdf
    assert '<option selected value="2013">' in pdf
    assert '<option selected value="5">' in pdf
    assert len(tf.pdf1.process_errors) == 0

    def failing_filter(*args, **kwargs):
        raise ValueError("ERROR!!!")

    test_form.pdf = PartialDateField("f", filters=[failing_filter])
    tf = test_form(DummyPostData({"pdf:year": "2012", "pdf:month": "4", "pdf:day": "12"}))
    assert len(tf.pdf.process_errors) > 0
    assert "ERROR!!!" in tf.pdf.process_errors


def test_partial_date_field_with_obj(test_form):

    tf = test_form(None, obj=MagicMock(pdf1=PD(2017, 1, 13)))
    pdf1 = tf.pdf1()

    assert '<option selected value="13">' in pdf1
    assert '<option value="">Year</option><option selected value="2017">2017</option>' in pdf1
    assert '<option value="">Month</option><option selected value="1">01</option><option value="2">' in pdf1

    tf = test_form(None, obj=MagicMock(pdf3=PD(2017)))
    pdf3 = tf.pdf3()

    assert '<option selected value="">' in pdf3
    assert '<option value="">Year</option><option selected value="2017">2017</option>' in pdf3
    assert '<option selected value="">Month</option><option value="1">01</option><option value="2">' in pdf3


def test_partial_date_field_with_data_and_obj(test_form):

    tf = test_form(DummyPostData({"pdf1:year": "2000"}), MagicMock(pdf1=PD(2017, 1, 13)))
    pdf1 = tf.pdf1()

    assert '<option selected value="13">' in pdf1
    assert '<option value="2001">2001</option><option selected value="2000">2000</option>' in pdf1
    assert '<option value="">Month</option><option selected value="1">01</option><option value="2">' in pdf1
