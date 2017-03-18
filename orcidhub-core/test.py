import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application import app
from config import client_id, authorization_base_url, scope, redirect_uri
import unittest
from peewee import SqliteDatabase


# import flask


class OrcidhubTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.db = SqliteDatabase(':memory:')
        self.app = app.test_client()

    def tearDown(self):
        pass

    def login(self, username, password):
        pass

    def test_index(self):
        rv = self.app.get("/")
        assert b"<!DOCTYPE html>" in rv.data
        # assert b"Home" in rv.data
        assert b"Royal Society of New Zealand" in rv.data, \
            "'Royal Society of New Zealand' should be present on the index page."

    """
    def test_ValidLogin(self):
        with self.app.session_transaction() as sess:
            sess['Auedupersonsharedtoken'] = "abc"
            sess['email'] = "admin@orcidhub.com"
            resp = self.app.get('/Tuakiri/login',
                                environ_base={'HTTP_SN': "surname_Test", 'HTTP_GIVENNAME': "givenName_Test",
                                              'HTTP_MAIL': "admin@orcidhub.com", 'HTTP_AUEDUPERSONSHAREDTOKEN': "abc",
                                              'HTTP_DISPLAYNAME': "ADMIN", 'HTTP_O': "Org_Test"})
            assert b"Affiliate yourself with ORCID HUB" in resp.data

    def test_InvalidLogin(self):
        with self.app.session_transaction() as sess:
            sess['Auedupersonsharedtoken'] = "abc"
            sess['email'] = "admin@orcidhub.com"
            resp = self.app.get('/Tuakiri/login',
                                environ_base={'HTTP_SN': "surname_Test", 'HTTP_GIVENNAME': "givenName_Test",
                                              'HTTP_MAIL': "admin@orcidhub.com"})
            assert b"<!DOCTYPE html>" in resp.data
            assert b"Home" in resp.data
            assert b"Royal Society of New Zealand" in resp.data, \
                "'Royal Society of New Zealand' should be present on the index page. """

    def test_demo(self):
        with self.app.session_transaction() as sess:
            sess['Auedupersonsharedtoken'] = "abc"
            sess['family_names'] = "paw"
            sess['given_names'] = "ros"
            sess['email'] = "get@orcidhub.org.nz"
            sess['client_id'] = client_id
            sess['scope'] = scope
            sess['redirect_uri'] = redirect_uri
            sess['authorization_base_url'] = authorization_base_url
            # resp = self.app.get('/Tuakiri/redirect')
            # assertRedirects(resp,"url")

    def test_auth(self):
        pass


if __name__ == '__main__':
    unittest.main()
