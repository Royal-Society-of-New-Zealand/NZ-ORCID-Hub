import pytest
from peewee import SqliteDatabase
from itertools import product
from models import User, Organisation, UserOrg, Role, OrcidToken
from playhouse.test_utils import test_database

@pytest.fixture
def test_db():
    """Peewee Test DB context.

    Example:

    def test_NAME(test_db):
        u = models.User(email="test@test.org", name="TESTER TESTERON")
        u.save()
        asser modls.User.count() == 1
    """
    _db = SqliteDatabase(":memory:")
    with test_database(_db, (Organisation, User, UserOrg, OrcidToken)) as _test_db:
        yield _test_db

    return


@pytest.fixture
def test_models(test_db, scope="session"):

    Organisation.insert_many((dict(
        name="Organisation #%d" % i,
        email="admin@org%d.org.nz" % i,
        tuakiri_name="Organisation #%d" % i,
        orcid_client_id="client-%d" % i,
        orcid_secret="secret-%d" % i,
        confirmed=(i % 2 == 0))
        for i in range(10))).execute()

    User.insert_many((dict(
        name="Test User #%d" % i,
        first_name="Test_%d" % i,
        last_name="User_%d" % i,
        email="user%d@org%d.org.nz" % (i, i * 4 % 10),
        edu_person_shared_token="EDU PERSON SHARED TOKEN #%d" % i,
        confirmed=(i % 3 != 0),
        roles=Role.SUPERUSER if i % 42 == 0 else Role.ADMIN if i % 13 == 0 else Role.RESEARCHER)
        for i in range(60))).execute()

    UserOrg.insert_many((dict(
        is_admin=((u + o) % 23 == 0),
        user=u,
        org=o) for (u, o) in product(range(2, 60, 4), range(2, 10)))).execute()

    UserOrg.insert_many((dict(
        is_admin=True,
        user=43,
        org=o) for o in range(1, 11))).execute()

    yield test_db


def test_user_org_link_user_constraint(test_models):
    org = Organisation.get(id=1)
    uo = UserOrg(user=999999, org=org)
    with pytest.raises(User.DoesNotExist):
        uo.save()


def test_user_org_link_org_constraint(test_models):
    user = User.get(id=1)
    uo = UserOrg(user=user, org=999999)
    with pytest.raises(Organisation.DoesNotExist):
        uo.save()


def test_org_count(test_models):
    assert Organisation.select().count() == 10


def test_user_count(test_models):
    assert User.select().count() == 60


def test_user_org_link(test_models):
    assert User.get(id=43).admin_for.count() == 10
    assert User.get(id=1).admin_for.count() == 0
    assert User.get(id=42).admin_for.count() > 0
    assert User.get(id=2).organisations.count() > 0
    assert Organisation.get(id=1).admins.count() == 1
    assert Organisation.get(id=5).users.count() > 0
    assert Organisation.get(id=5).admins.count() > 0
