from itertools import product

import pytest
from peewee import Model, SqliteDatabase
from playhouse.test_utils import test_database

from .models import (Affiliation, AffiliationRecord, ModelException, OrcidToken, Organisation,
                     OrgInfo, PartialDate, PartialDateField, Role, Task, User, UserOrg,
                     UserOrgAffiliation, create_tables, drop_tables)


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
    with test_database(
            _db,
        (Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, Task, AffiliationRecord),
            fail_silently=True) as _test_db:
        yield _test_db

    return


@pytest.fixture
def test_models(test_db):

    Organisation.insert_many((dict(
        name="Organisation #%d" % i,
        tuakiri_name="Organisation #%d" % i,
        orcid_client_id="client-%d" % i,
        orcid_secret="secret-%d" % i,
        confirmed=(i % 2 == 0)) for i in range(10))).execute()

    User.insert_many((dict(
        name="Test User #%d" % i,
        first_name="Test_%d" % i,
        last_name="User_%d" % i,
        email="user%d@org%d.org.nz" % (i, i * 4 % 10),
        confirmed=(i % 3 != 0),
        roles=Role.SUPERUSER if i % 42 == 0 else Role.ADMIN if i % 13 == 0 else Role.RESEARCHER)
                      for i in range(60))).execute()

    UserOrg.insert_many((dict(is_admin=((u + o) % 23 == 0), user=u, org=o)
                         for (u, o) in product(range(2, 60, 4), range(2, 10)))).execute()

    UserOrg.insert_many((dict(is_admin=True, user=43, org=o) for o in range(1, 11))).execute()

    OrcidToken.insert_many((dict(
        user=User.get(id=1),
        org=Organisation.get(id=1),
        scope="/read-limited",
        access_token="Test_%d" % i) for i in range(60))).execute()

    UserOrgAffiliation.insert_many((dict(
        user=User.get(id=1),
        organisation=Organisation.get(id=1),
        department_name="Test_%d" % i,
        department_city="Test_%d" % i,
        role_title="Test_%d" % i,
        path="Test_%d" % i,
        put_code="%d" % i) for i in range(30))).execute()

    yield test_db


def test_user_uuid():
    u = User(email="test@gtest.com")
    assert str(u.uuid) == "8428e5f6-38c6-530f-8339-9aeffb99e022"


def test_user_org_link_user_constraint(test_models):
    org = Organisation.get(id=1)
    uo = UserOrg(user_id=999999, org=org)
    with pytest.raises(User.DoesNotExist):
        uo.save()


def test_user_org_link_org_constraint(test_models):
    user = User.get(id=1)
    uo = UserOrg(user=user, org_id=999999)
    with pytest.raises(Organisation.DoesNotExist):
        uo.save()


def test_org_count(test_models):
    assert Organisation.select().count() == 10


def test_user_count(test_models):
    assert User.select().count() == 60


def test_orcidtoken_count(test_models):
    assert OrcidToken.select().count() == 60


def test_user_oganisation_affiliation_count(test_models):
    assert UserOrgAffiliation.select().count() == 30


def test_user_org_link(test_models):
    assert User.get(id=43).admin_for.count() == 10
    assert User.get(id=1).admin_for.count() == 0
    assert User.get(id=42).admin_for.count() > 0
    assert User.get(id=2).organisations.count() > 0
    assert Organisation.get(id=1).admins.count() == 1
    assert Organisation.get(id=5).users.count() > 0
    assert Organisation.get(id=5).admins.count() > 0


def test_roles(test_models):
    assert Role.RESEARCHER == "RESEARCHER"
    assert Role.RESEARCHER == Role["RESEARCHER"]
    assert Role.RESEARCHER != "ADMIN"
    assert Role.RESEARCHER != Role["ADMIN"]
    assert hash(Role.RESEARCHER) == hash("RESEARCHER")


def test_user_roles(test_models):
    user = User(
        name="Test User ABC123",
        first_name="ABC",
        last_name="123",
        email="user_abc_123@org.org.nz",
        confirmed=True,
        roles=Role.ADMIN | Role.RESEARCHER)

    assert user.has_role(Role.ADMIN)
    assert user.has_role("ADMIN")
    assert user.has_role(Role.RESEARCHER)
    assert user.has_role("RESEARCHER")
    assert user.has_role(Role.RESEARCHER | Role.ADMIN)
    assert user.has_role(4)
    assert user.has_role(2)

    assert not user.has_role(Role.SUPERUSER)
    assert not user.has_role("SUPERUSER")
    assert not user.has_role(1)

    assert not user.has_role("NOT A ROLE")
    assert not user.has_role(~(1 | 2 | 4 | 8 | 16))

    assert not user.has_role(1.1234)


def test_admin_is_admin(test_models):
    user = User(
        name="Test User ABC123",
        first_name="ABC",
        last_name="123",
        email="user_abc_123@org.org.nz",
        confirmed=True,
        roles=Role.ADMIN | Role.RESEARCHER)

    assert user.is_admin


def test_drop_tables(test_models):
    drop_tables()
    assert not User.table_exists()
    assert not Organisation.table_exists()
    assert not UserOrg.table_exists()


def test_create_tables(test_models):
    drop_tables()
    create_tables()
    assert User.table_exists()
    assert Organisation.table_exists()
    assert UserOrg.table_exists()


def test_partial_date():
    pd = PartialDate.create({"year": {"value": "2003"}})
    assert pd.as_orcid_dict() == {'year': {'value': '2003'}, 'month': None, 'day': None}
    assert pd.year == 2003
    pd = PartialDate.create({
        "year": {
            "value": "2003"
        },
        "month": {
            "value": '07'
        },
        "day": {
            "value": '31'
        }
    })
    assert pd.as_orcid_dict() == {
        'year': {
            'value': '2003'
        },
        'month': {
            "value": '07'
        },
        'day': {
            "value": '31'
        }
    }
    assert pd.year == 2003 and pd.month == 7 and pd.day == 31
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

    with pytest.raises(ModelException):
        PartialDate.create("ABC")


def test_pd_field():

    db = SqliteDatabase(":memory:")

    class TestModel(Model):
        pf = PartialDateField(null=True)

        class Meta:
            database = db

    TestModel.create_table()
    TestModel(pf=PartialDate()).save()
    TestModel(pf=None).save()
    res = [r[0] for r in db.execute_sql("SELECT pf FROM testmodel").fetchall()]
    assert res[0] is None and res[1] is None
    TestModel(pf=PartialDate(1997)).save()
    TestModel(pf=PartialDate(1996, 4)).save()
    TestModel(pf=PartialDate(1995, 5, 13)).save()
    res = [r[0] for r in db.execute_sql("SELECT pf FROM testmodel").fetchall()]
    assert '1995-05-13' in res
    assert '1996-04-**' in res
    assert '1997-**-**' in res

    res = [r.pf for r in TestModel.select().order_by(TestModel.pf)]
    assert res[0] is None
    assert res[1] is None
    assert res[2] == PartialDate(1995, 5, 13)
    assert res[3] == PartialDate(1996, 4)
    assert res[4] == PartialDate(1997)


def test_load_org_info_from_csv(test_models):
    # flake8: noqa
    OrgInfo.load_from_csv(
        """Organisation,Title,First Name,Last Name,Role,Email,Phone,Permission to post to web,Country Code,City of home campus,common:disambiguated-organization-identifier,common:disambiguation-source
Organisation_0,Title_0,First Name_0,Last Name_0,Role_0,Email_0,Phone_0,Permission to post to web_0,Country Code_0,City of home campus_0,common:disambiguated-organization-identifier_0,common:disambiguation-source
Organisation_1,Title_1,First Name_1,Last Name_1,Role_1,Email_1,Phone_1,yes,Country Code_1,City of home campus_1,common:disambiguated-organization-identifier_1,common:disambiguation-source
""")
    assert OrgInfo.select().count() == 2
    oi = OrgInfo.get(name="Organisation_1")
    assert oi.is_public


def test_affiliations(test_models):
    assert Affiliation.EDU == "EDU"
    assert Affiliation.EMP == "EMP"
    assert Affiliation.EMP == Affiliation["EMP"]
    assert hash(Affiliation.EMP) == hash("EMP")
    assert str(Affiliation.EDU | Affiliation.EMP) == "Education, Employment"


def test_field_is_updated(test_db):
    u = User.create(email="test@test.com", name="TESTER")
    u.save()
    assert not u.field_is_updated("name")
    u.name = "NEW VALUE"
    assert u.field_is_updated("name")


def test_load_task_from_csv(test_models):
    org = Organisation.create(name="TEST0")
    # flake8: noqa
    test = Task.load_from_csv(
        """First name	Last name	email address	Organisation	Campus/Department	City	Course or Job title	Start date	End date	Student/Staff
FNA	LBA	aaa.lnb@test.com	TEST1	Research Funding	Wellington	Programme Manager - ORCID	2016-09		Staff
FNA	LBA	aaa.lnb@test.com	TEST1	Research Funding	Wellington	Programme Manager - Insights and Evaluation	2014		Staff
FNA	LBA	aaa.lnb@test.com	TEST0	External Affairs	Wellington	Senior Evaluation Officer	2011	2014	Staff
FNA	LBA	aaa.lnb@test.com	TEST0	Policy and Evaluation	Wellington	Evaluation Officer	2005	2011	Staff
FNA	LBA	aaa.lnb@test.com	TEST0	Marsden Fund	Wellington	Research Assessor	2001	2004	Staff
FNB	LNB	b.b@test.com	TEST1	Communications and Outreach	Wellington	Projects and Events Coordinator	2013		Staff
FNB	LNB	b.b@test.com	TEST0	Science and Education Group	Wellington	School Programmes Manager	2008	2013	Staff
FNB	LNB	b.b@test.com	TEST0	Science and Education Group	Wellington	Project Manager	2000	2004	Staff
FNB	LNB	b.b@test.com	TEST0	Science and Education Group	Wellington	Manager Special Programmes	2004	2008	Staff
""",
        filename="TEST.tsv",
        org=org)
    assert test.record_count == 9
    assert AffiliationRecord.select().count() == test.record_count


def test_is_superuser():
    su = User(roles=Role.SUPERUSER)
    assert su.is_superuser
    su.is_superuser = False
    assert not su.has_role(Role.SUPERUSER)

    u = User()
    assert not u.is_superuser
    assert not u.has_role(Role.SUPERUSER)
    u.is_superuser = True
    assert u.is_superuser
    assert u.has_role(Role.SUPERUSER)
