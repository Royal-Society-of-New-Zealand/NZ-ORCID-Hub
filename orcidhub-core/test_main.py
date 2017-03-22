from models import User, Organisation, UserOrg
from flask_login import login_user, current_user
import pprint
import pytest


def test_index(client):
    rv = client.get("/")
    assert b"<!DOCTYPE html>" in rv.data
    # assert b"Home" in rv.data
    assert b"Royal Society of New Zealand" in rv.data, \
        "'Royal Society of New Zealand' should be present on the index page."


def get_response(request_ctx):
    """
    Return response within the request context
    It should be used with the request context.
    """
    app = request_ctx.app
    # call the before funcs
    rv = app.preprocess_request()
    if rv is not None:
        response = app.make_response(rv)
    else:
        # do the main dispatch
        rv = app.dispatch_request()
        response = app.make_response(rv)

        # now do the after funcs
        response = app.process_response(response)

    return response


def test_login(request_ctx):
    with request_ctx("/") as ctx:
        test_user = User(
            name="TEST USER",
            email="test@test.test.net",
            username="test42",
            confirmed=True)
        login_user(test_user, remember=True)

        rv = get_response(ctx)
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"TEST USER" in rv.data, "Expected to have the user name on the page"
        assert b"test@test.test.net" in rv.data, "Expected to have the user email on the page"


@pytest.mark.parametrize("url", [
    # "/admin",
    "/link",
    "/auth",
    # "/logout",
    "/pyinfo",
    "/reset_db",
    # "/uoa-slo",
    "/invite/organisation",
    "/invite/user"])
def test_access(url, client):
    rv = client.get(url)
    assert rv.status_code == 302
    assert "Location" in rv.headers, pprint.pformat(rv.headers, indent=4)
    assert "next=" in rv.location
    rv = client.get(url, follow_redirects=True)
    assert rv.status_code == 200
    assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
    assert b"Please log in to access this page." in rv.data

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


def test_tuakiri_login(client):
    """
    After getting logged in a new user entry shoulg be created
    """
    rv = client.get("/Tuakiri/login",
                    headers={
                        "Auedupersonsharedtoken": "ABC123",
                        "Sn": "LAST NAME/SURNAME/FAMILY NAME",
                        'Givenname': "FIRST NAME/GIVEN NAME",
                        "Mail": "user@test.test.net",
                        "O": "ORGANISATION 123",
                        "Displayname": "TEST USER FROM 123"})

    assert rv.status_code == 302
    u = User.get(email="user@test.test.net")
    assert u.name == "TEST USER FROM 123", "Expected to have the user in the DB"
    assert u.first_name == "FIRST NAME/GIVEN NAME"
    assert u.last_name == "LAST NAME/SURNAME/FAMILY NAME"
    assert u.edu_person_shared_token == "ABC123"

    assert current_user.name == "TEST USER FROM 123"
    assert current_user.edu_person_shared_token == "ABC123"


def test_tuakiri_login_wo_org(client):
    """
    If a user logs in from an organisation that isn't
    onboared, the user should be informed about that and
    redirected to the login page.
    """

    rv = client.get("/Tuakiri/login",
                    headers={
                        "Auedupersonsharedtoken": "ABC999",
                        "Sn": "LAST NAME/SURNAME/FAMILY NAME",
                        'Givenname': "FIRST NAME/GIVEN NAME",
                        "Mail": "user@test.test.net",
                        "O": "INCOGNITO",
                        "Displayname": "TEST USER FROM UNKNOWN"},
                    follow_redirects=True)

    u = User.get(email="user@test.test.net")
    assert u.edu_person_shared_token == "ABC999"
    assert b"Your organisation (INCOGNITO) is not onboarded" in rv.data


def test_tuakiri_login_with_org(client):
    """
    If a user logs in from an organisation that isn't
    onboared, the user should be informed about that and
    redirected to the login page.
    """

    org = Organisation(name="THE ORGANISATION")
    org.save()

    rv = client.get("/Tuakiri/login",
                    headers={
                        "Auedupersonsharedtoken": "ABC111",
                        "Sn": "LAST NAME/SURNAME/FAMILY NAME",
                        'Givenname': "FIRST NAME/GIVEN NAME",
                        "Mail": "user111@test.test.net",
                        "O": "THE ORGANISATION",
                        "Displayname": "TEST USER FROM THE ORGANISATION"},
                    follow_redirects=True)

    u = User.get(email="user111@test.test.net")
    assert u.organisation == org
    assert org in u.organisations
    assert u.edu_person_shared_token == "ABC111"
    assert b"Your organisation (INCOGNITO) is not onboarded" not in rv.data
    uo = UserOrg.get(user=u, org=org)
    assert not uo.is_admin
