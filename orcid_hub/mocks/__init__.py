"""External service mocking."""

from flask import Blueprint, render_template, abort, request, session, redirect
from os import path, remove
from tempfile import gettempdir
import base64
import pickle
import zlib
from urllib.parse import urlsplit

TEST_DATA = {
    "test123@test.net": {
        "Eppn": "178623242@test.net",
        "Affiliation": "staff,student",
        "Unscoped-Affiliation": "staff,student",
        "Entitlement": "",
        "Targeted-Id": "",
        "Persistent-Id": "N/A",
        "O": "University of Testing",
        "Sn": "Teseer",
        "Cn": "John Tester",
        "Givenname": "John",
        "Displayname": "Rad Bloggs",
        "Ou": "TESTING DEPARTMENT",
        "Telephonenumber": "+64 12345678",
        "Assurance": "",
        "Primary-Affiliation": "",
        "Auedupersonsharedtoken": "ihVL5ToRexj-Qf9as0fdnf0FvDQ",
        "Mobile": "+64 0434723643",
        "Uid": "194624382",
        "Shib-Application-Id": "default",
    },
    "admin123@test.net": {
        "Eppn": "178623242@test.net",
        "Affiliation": "staff,student",
        "Unscoped-Affiliation": "staff,student",
        "Entitlement": "",
        "Targeted-Id": "",
        "Persistent-Id": "N/A",
        "O": "University of Testing",
        "Sn": "Teseer",
        "Cn": "John Tester",
        "Givenname": "John",
        "Displayname": "Rad Bloggs",
        "Ou": "TESTING DEPARTMENT",
        "Telephonenumber": "+64 12345678",
        "Assurance": "",
        "Primary-Affiliation": "",
        "Auedupersonsharedtoken": "ihVL5ToRexj-Qf9as0fdnf0FvDQ",
        "Mobile": "+64 0434723643",
        "Uid": "194624382",
        "Shib-Application-Id": "default",
    },
}

mocks = Blueprint(
    "mocks", __name__, url_prefix="/mocks", template_folder="templates", static_folder="static")


def get_next_url():
    """Retrieve and sanitize next/return URL."""
    _next = request.args.get("next") or request.args.get("_next") or request.referrer

    if _next and ("orcidhub.org.nz" in _next or _next.startswith("/") or "127.0" in _next
                  or "c9users.io" in _next or "localhost" in _next):
        return _next
    return None


@mocks.route("/sp/attributes/<string:key>")
def get_attributes(key):
    """Retrieve SAML attributes."""
    data = ''
    data_filename = path.join(gettempdir(), key)
    try:
        with open(data_filename, 'rb') as kf:
            data = kf.read()
        remove(data_filename)
    except Exception as ex:
        abort(403, ex)
    return data


@mocks.route("/sp")
def shib_sp():
    """Remote Shibboleth authenitication handler mock.

    It presenst a mock for selecting an organisation and redirects to
    a login form mock.
    """
    _next = get_next_url()
    _key = request.args.get("key")
    session["external-sp-mock"] = {
        "next": _next,
        "key": _key,
    }
    if _next:
        return render_template("select_home_organisation.html")

    abort(403)


@mocks.route(
    "/iam", methods=[
        "GET",
        "POST",
    ])
def iam():
    """Identity and access management (IAM) mock.

    It presenst a mock for selecting an organisation and redirects to
    a login form mock.
    """
    if request.method == "GET":
        return render_template("mocks_login.html")
    elif request.method == "POST":
        s = session["external-sp-mock"]
        _next = s["next"]
        _key = s["key"]
        email = request.form.get("username")

        idp = request.args.get("origin", "http://iam.mock.net/idp")
        domainname = urlsplit(idp).netloc

        data = {k: v for k, v in request.headers.items()}
        data.update({
            "Shib-Cookie-Name":
            "NO NAME",
            "Shib-Session-Id":
            "_bc79355832c457a3b70e9322890b74d7",
            "Shib-Session-Index":
            "_67c1daeffa1fc862d1e54ecb3e37ace1",
            "Shib-Identity-Provider":
            idp,
            "Shib-Authentication-Method":
            "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            "Shib-Authentication-Instant":
            "2017-12-04T05:24:44.405Z",
            "Shib-Authncontext-Class":
            "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            "Shib-Authncontext-Decl":
            "",
            "Shib-Assertion-Count":
            "",
            "Shib-Handler":
            "N/A",
            "Affiliation":
            "",
            "Unscoped-Affiliation":
            "",
            "Entitlement":
            "",
            "Targeted-Id":
            "",
            "Persistent-Id":
            "N/A",
            "O":
            "",
            "Sn":
            "Bloggs",
            "Cn":
            "Rad Bloggs",
            "Givenname":
            "Rad",
            "Mail":
            email,
            "Displayname":
            "",
            "Ou":
            "",
            "Telephonenumber":
            "",
            "Assurance":
            "",
            "Primary-Affiliation":
            "",
            "Auedupersonsharedtoken":
            "",
            "Auedupersonlegalname":
            "",
            "Auedupersonaffiliation":
            "",
            "Mobile":
            "",
            "Uid":
            "",
            "Postaladdress":
            "",
            "Homeorganization":
            "",
            "Homeorganizationtype":
            "",
            "Shib-Application-Id":
            "default",
        })

        if email in TEST_DATA:
            data.update(TEST_DATA[email])
        else:
            from faker import Faker
            fake = Faker()
            fn, ln = fake.first_name(), fake.last_name()
            cn = fn + ' ' + ln
            affiliation = fake.random.choice(["faculty", "staff", "student"])
            data.update({
                "Eppn": email.split("@")[0] + '@' + domainname,
                "Affiliation": affiliation,
                "Unscoped-Affiliation": affiliation,
                "Entitlement": "",
                "Targeted-Id": "",
                "Persistent-Id": "N/A",
                "O": fake.company(),
                "Sn": ln,
                "Cn": cn,
                "Givenname": fn,
                "Mail": email,
                "Displayname": cn,
                "Telephonenumber": fake.phone_number(),
                "Mobile": fake.phone_number(),
                "Uid": fake.random.randint(1000000, 9999999),
                "Postaladdress": fake.address(),
            })

        data = base64.b64encode(zlib.compress(pickle.dumps(data)))

        resp = redirect(_next)
        with open(path.join(gettempdir(), _key), 'wb') as kf:
            kf.write(data)

        return resp
    abort(403)
