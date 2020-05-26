# -*- coding: utf-8 -*-
"""Tests for util functions."""

import pytest
from portal.utils.date_utils import PartialDate


def test_partial_date():
    pd = PartialDate.create({"year": {"value": "2003"}})
    with pytest.raises(TypeError):
        pd.as_datetime()
    assert pd.as_orcid_dict() == {"year": {"value": "2003"}, "month": None, "day": None}
    assert pd.year == 2003
    pd = PartialDate.create(
        {"year": {"value": "2003"}, "month": {"value": "07"}, "day": {"value": "31"}}
    )
    assert pd.as_orcid_dict() == {
        "year": {"value": "2003"},
        "month": {"value": "07"},
        "day": {"value": "31"},
    }
    assert pd.year == 2003 and pd.month == 7 and pd.day == 31

    pd = PartialDate.create(
        {"year": {"value": "2003"}, "month": {"value": "11"}, "day": {"value": None}}
    )
    assert pd.year == 2003 and pd.month == 11 and pd.day is None

    pd = PartialDate.create(
        {"year": {"value": "2003"}, "month": {"value": None}, "day": {"value": None}}
    )
    assert pd.year == 2003 and pd.month is None and pd.day is None

    assert PartialDate().as_orcid_dict() is None
    assert PartialDate.create(None) is None
    assert PartialDate.create({}) is None
    assert PartialDate.create("1997") == PartialDate(year=1997, month=None, day=None)
    assert PartialDate.create("1997-12") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997-12-31") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("1997/12") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997/12/31") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("12/1997") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("31/12/1997") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("1997.12") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997.12.31") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("12.1997") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("31.12.1997") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("5.03.2018") == PartialDate(year=2018, month=3, day=5)
    assert PartialDate.create("1997 12:00:00 PM") == PartialDate(year=1997, month=None, day=None)
    assert PartialDate.create("1997-12 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997-12-31 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("1997/12 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997/12/31 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("12/1997 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("31/12/1997 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("6/08/2017 12:00:00 PM") == PartialDate(year=2017, month=8, day=6)
    assert PartialDate.create("1997.12 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997.12.31 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("12.1997 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("31.12.1997 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("6.08.2017 12:00:00 PM") == PartialDate(year=2017, month=8, day=6)

    with pytest.raises(ModelException):
        PartialDate.create("ABC")

    pd = PartialDate(2003, 12, 31)
    assert pd.as_datetime() == datetime(2003, 12, 31)

    pd = PartialDate()
    assert str(pd) == ""
