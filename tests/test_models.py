# -*- coding: utf-8 -*-
"""Tests for models."""

from datetime import datetime
from itertools import product

import pytest
from peewee import Model, SqliteDatabase

from orcid_hub.models import *
from orcid_hub.models import app as _app


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
    assert User.select().count() == 63


def test_orcidtoken_count(test_models):
    assert OrcidToken.select().count() == 60


def test_AffiliationRecord_count(test_models):
    assert AffiliationRecord.select().count() == 10


def test_FundingRecord_count(test_models):
    assert FundingRecord.select().count() == 10


def test_FundingContributor_count(test_models):
    assert FundingContributor.select().count() == 10


def test_FundingInvitees_count(test_models):
    assert FundingInvitees.select().count() == 10


def test_ExternalId_count(test_models):
    assert ExternalId.select().count() == 10


def test_WorkRecord_count(test_models):
    assert WorkRecord.select().count() == 10


def test_WorkContributor_count(test_models):
    assert WorkContributor.select().count() == 10


def test_WorkExternalId_count(test_models):
    assert WorkExternalId.select().count() == 10


def test_WorkInvitees_count(test_models):
    assert WorkInvitees.select().count() == 10


def test_PeerReviewRecord_count(test_models):
    assert PeerReviewRecord.select().count() == 10


def test_PeerReviewExternalId_count(test_models):
    assert PeerReviewExternalId.select().count() == 10

def test_PeerReviewInvitees_count(test_models):
    assert PeerReviewInvitee.select().count() == 10

def test_Task_count(test_models):
    assert Task.select().count() == 30


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
    assert len(User.get(email="user_the_same_id_0@org0.org.nz").linked_accounts) == 3

    user = User.get(email="user0@org0.org.nz")
    available_organisations = user.available_organisations
    assert available_organisations.count() == 10


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
    with pytest.raises(TypeError):
        pd.as_datetime()
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
    assert PartialDate.create("1997 12:00:00 PM") == PartialDate(year=1997, month=None, day=None)
    assert PartialDate.create("1997-12 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997-12-31 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("1997/12 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("1997/12/31 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("12/1997 12:00:00 PM") == PartialDate(year=1997, month=12, day=None)
    assert PartialDate.create("31/12/1997 12:00:00 PM") == PartialDate(year=1997, month=12, day=31)
    assert PartialDate.create("6/08/2017 12:00:00 PM") == PartialDate(year=2017, month=8, day=6)

    with pytest.raises(ModelException):
        PartialDate.create("ABC")

    pd = PartialDate(2003, 12, 31)
    assert pd.as_datetime() == datetime(2003, 12, 31)

    pd = PartialDate()
    assert str(pd) == ""


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
    assert AffiliationRecord.select().count(
    ) == test.record_count + 10  # The 10 value is from already inserted entries.


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


def test_validate_orcid_id():
    assert validate_orcid_id(None) is None
    assert validate_orcid_id(0) is None
    assert validate_orcid_id("") is None
    assert validate_orcid_id("0000-0000-0000-00X3") is None
    with pytest.raises(ValueError):
        validate_orcid_id("123")
    with pytest.raises(ValueError):
        validate_orcid_id("0000-0000-0000-00X4")


def test_boolean_field():

    class TestTableWithBooleanField(BaseModel):
        test_field = BooleanField()

        class Meta:
            database = SqliteDatabase(":memory:")

    TestTableWithBooleanField.create_table()
    TestTableWithBooleanField.create(test_field=True)
    assert TestTableWithBooleanField.select().where(
        TestTableWithBooleanField.test_field.NOT()).count() == 0


def test_base_model_to_dict():
    """Test base model features."""
    class TestTable(BaseModel):
        test_field = TextField()

        class Meta:
            database = SqliteDatabase(":memory:")

    TestTable.create_table()
    TestTable.create(test_field="ABC123")

    rec = TestTable.select().first()
    assert rec.to_dict() == {"id": 1, "test_field": "ABC123"}

    rec = TestTable.get(1)
    assert rec.test_field == "ABC123"
