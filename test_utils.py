# -*- coding: utf-8 -*-
"""Tests for util functions."""

import utils


def test_append_qs():
    """Test URL modication."""
    assert utils.append_qs(
        "https://abc.com/bar?p=foo", abc=123,
        p2="ABC") == "https://abc.com/bar?p=foo&abc=123&p2=ABC"
    assert utils.append_qs(
        "https://abc.com/bar", abc=123, p2="ABC") == "https://abc.com/bar?abc=123&p2=ABC"
    assert utils.append_qs(
        "https://abc.com/bar?p=foo", p2="A&B&C D") == "https://abc.com/bar?p=foo&p2=A%26B%26C+D"
