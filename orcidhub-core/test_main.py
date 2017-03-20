import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, login_user
from models import User
from config import client_id, authorization_base_url, scope, redirect_uri
import unittest


class OrcidhubTestCase(unittest.TestCase):
    def setUp(self):
        global db
        self.app = app
        app.config['TESTING'] = True
        self.client = app.test_client()
        # models.db = SqliteDatabase(":memory:")  # TODO: set db via DB URI
        # or create a separate DB for unittesting
        # models.create_tables()

    def tearDown(self):
        pass

    def login(self, username, password):
        pass

    def get_response(self):
        """
        Return response within the request context
        It should be used with the request context.
        """
        # call the before funcs
        rv = self.app.preprocess_request()
        if rv is not None:
            response = self.app.make_response(rv)
        else:
            # do the main dispatch
            rv = self.app.dispatch_request()
            response = self.app.make_response(rv)

            # now do the after funcs
            response = self.app.process_response(response)

        return response

    def test_login(self):
        with app.test_request_context("/"):
            self.test_user = User(
                name="TEST USER",
                email="test@test.test.net",
                username="test42",
                confirmed=True)
            login_user(self.test_user, remember=True)

            rv = self.get_response()
            assert b"<!DOCTYPE html>" in rv.data
            assert b"TEST USER" in rv.data

    def test_index(self):
        rv = self.client.get("/")
        assert b"<!DOCTYPE html>" in rv.data
        # assert b"Home" in rv.data
        assert b"Royal Society of New Zealand" in rv.data, \
            "'Royal Society of New Zealand' should be present on the index page."

    """
    def test_ValidLogin(self):
        with self.client.session_transaction() as sess:
            sess['Auedupersonsharedtoken'] = "abc"
            sess['email'] = "admin@orcidhub.com"
            resp = self.client.get('/Tuakiri/login',
                                environ_base={'HTTP_SN': "surname_Test", 'HTTP_GIVENNAME': "givenName_Test",
                                              'HTTP_MAIL': "admin@orcidhub.com", 'HTTP_AUEDUPERSONSHAREDTOKEN': "abc",
                                              'HTTP_DISPLAYNAME': "ADMIN", 'HTTP_O': "Org_Test"})
            assert b"Affiliate yourself with ORCID HUB" in resp.data

    def test_InvalidLogin(self):
        with self.client.session_transaction() as sess:
            sess['Auedupersonsharedtoken'] = "abc"
            sess['email'] = "admin@orcidhub.com"
            resp = self.client.get('/Tuakiri/login',
                                environ_base={'HTTP_SN': "surname_Test", 'HTTP_GIVENNAME': "givenName_Test",
                                              'HTTP_MAIL': "admin@orcidhub.com"})
            assert b"<!DOCTYPE html>" in resp.data
            assert b"Home" in resp.data
            assert b"Royal Society of New Zealand" in resp.data, \
                "'Royal Society of New Zealand' should be present on the index page. """

    def test_demo(self):
        with self.client.session_transaction() as sess:
            sess['Auedupersonsharedtoken'] = "abc"
            sess['family_names'] = "paw"
            sess['given_names'] = "ros"
            sess['email'] = "get@orcidhub.org.nz"
            sess['client_id'] = client_id
            sess['scope'] = scope
            sess['redirect_uri'] = redirect_uri
            sess['authorization_base_url'] = authorization_base_url
            # resp = self.client.get('/Tuakiri/redirect')
            # assertRedirects(resp,"url")

    def test_auth(self):
        pass


if __name__ == '__main__':
    unittest.main()
