import json
import os
from datetime import datetime
from io import StringIO
from itertools import product

import pytest
from peewee import Model, SqliteDatabase
from playhouse.test_utils import test_database

from orcid_hub import JSONEncoder
from orcid_hub.models import (
    Affiliation, AffiliationRecord, BaseModel, BooleanField, ExternalId, File, ForeignKeyField,
    FundingContributor, FundingInvitee, FundingRecord, Log, ModelException, NestedDict, OrcidToken,
    Organisation, OrgInfo, OtherNameRecord, PartialDate, PartialDateField, PeerReviewExternalId,
    PeerReviewInvitee, PeerReviewRecord, ResearcherUrlRecord, Role, Task, TaskType, TaskTypeField,
    TextField, User, UserInvitation, UserOrg, UserOrgAffiliation, WorkContributor, WorkExternalId,
    WorkInvitee, WorkRecord, create_tables, drop_tables, load_yaml_json, validate_orcid_id)


@pytest.fixture
def testdb():
    """Peewee Test DB context.

    Example:

    def test_NAME(testdb):
        u = models.User(email="test@test.org", name="TESTER TESTERON")
        u.save()
        asser modls.User.count() == 1
    """
    _db = SqliteDatabase(":memory:", pragmas=[("foreign_keys", "on")])
    with test_database(
            _db, (Organisation, File, User, UserInvitation, UserOrg, OtherNameRecord, OrgInfo,
                  OrcidToken, UserOrgAffiliation, Task, AffiliationRecord, ExternalId,
                  FundingRecord, FundingContributor, FundingInvitee, WorkRecord, WorkContributor,
                  WorkExternalId, WorkInvitee, PeerReviewRecord, PeerReviewExternalId,
                  PeerReviewInvitee, ResearcherUrlRecord),
            fail_silently=True) as _test_db:
        yield _test_db

    return


@pytest.fixture
def models(testdb):

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

    User.insert_many((dict(
        name="Test User with ORCID ID 'ABC-123' #%d" % i,
        orcid="ABC-123",
        first_name="Test_%d" % i,
        last_name="User_%d" % i,
        email="user_the_same_id_%d@org%d.org.nz" % (i, i),
        confirmed=True,
        organisation=(i + 1),
        roles=Role.RESEARCHER) for i in range(3))).execute()

    UserOrg.insert_many(
        dict(user=u.id, org=u.organisation_id)
        for u in User.select().where(User.orcid == "ABC-123")).execute()

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

    Task.insert_many((dict(
        org=Organisation.get(id=1),
        created_by=User.get(id=1),
        updated_by=User.get(id=1),
        filename="Test_%d" % i,
        task_type=0) for i in range(30))).execute()

    AffiliationRecord.insert_many((dict(
        is_active=False,
        task=Task.get(id=1),
        put_code=90,
        external_id="Test_%d" % i,
        status="Test_%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        email="Test_%d" % i,
        orcid="123112311231%d" % i,
        organisation="Test_%d" % i,
        affiliation_type="Test_%d" % i,
        role="Test_%d" % i,
        department="Test_%d" % i,
        city="Test_%d" % i,
        state="Test_%d" % i,
        country="Test_%d" % i,
        disambiguated_id="Test_%d" % i,
        disambiguation_source="Test_%d" % i) for i in range(10))).execute()

    ResearcherUrlRecord.insert_many((dict(
        is_active=False,
        task=Task.get(id=1),
        put_code=90,
        status="Test_%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        email="Test_%d" % i,
        orcid="123112311231%d" % i,
        url_name="Test_%d" % i,
        url_value="Test_%d" % i,
        visibility="Test_%d" % i,
        display_index=i) for i in range(10))).execute()

    OtherNameRecord.insert_many((dict(
        is_active=False,
        task=Task.get(id=1),
        put_code=90,
        status="Test_%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        email="Test_%d" % i,
        orcid="123112311231%d" % i,
        content="Test_%d" % i,
        visibility="Test_%d" % i,
        display_index=i) for i in range(10))).execute()

    FundingRecord.insert_many((dict(
        task=Task.get(id=1),
        title="Test_%d" % i,
        translated_title="Test_%d" % i,
        translated_title_language_code="Test_%d" % i,
        type="Test_%d" % i,
        organization_defined_type="Test_%d" % i,
        short_description="Test_%d" % i,
        amount="Test_%d" % i,
        currency="Test_%d" % i,
        org_name="Test_%d" % i,
        city="Test_%d" % i,
        region="Test_%d" % i,
        country="Test_%d" % i,
        disambiguated_org_identifier="Test_%d" % i,
        disambiguation_source="Test_%d" % i,
        is_active=False,
        status="Test_%d" % i) for i in range(10))).execute()

    FundingContributor.insert_many((dict(
        funding_record=FundingRecord.get(id=1),
        orcid="123112311231%d" % i,
        name="Test_%d" % i,
        role="Test_%d" % i) for i in range(10))).execute()

    FundingInvitee.insert_many((dict(
        funding_record=FundingRecord.get(id=1),
        orcid="123112311231%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        put_code=i,
        status="Test_%d" % i,
        identifier="%d" % i,
        visibility="Test_%d" % i,
        email="Test_%d" % i) for i in range(10))).execute()

    ExternalId.insert_many((dict(
        funding_record=FundingRecord.get(id=1),
        type="Test_%d" % i,
        value="Test_%d" % i,
        url="Test_%d" % i,
        relationship="Test_%d" % i) for i in range(10))).execute()

    PeerReviewRecord.insert_many((dict(
        task=Task.get(id=1),
        review_group_id="issn:1212_%d" % i,
        reviewer_role="reviewer_%d" % i,
        review_url="xyz_%d" % i,
        review_type="REVIEW_%d" % i,
        subject_external_id_type="doi_%d" % i,
        subject_external_id_value="1212_%d" % i,
        subject_external_id_url="url/SELF_%d" % i,
        subject_external_id_relationship="SELF_%d" % i,
        subject_container_name="Journal title_%d" % i,
        subject_type="JOURNAL_ARTICLE_%d" % i,
        subject_name_title="name_%d" % i,
        subject_name_subtitle="subtitle_%d" % i,
        subject_name_translated_title_lang_code="en",
        subject_name_translated_title="sdsd_%d" % i,
        subject_url="url_%d" % i,
        convening_org_name="THE ORGANISATION_%d" % i,
        convening_org_city="auckland_%d" % i,
        convening_org_region="auckland_%d" % i,
        convening_org_country="nz_%d" % i,
        convening_org_disambiguated_identifier="123_%d" % i,
        convening_org_disambiguation_source="1212_%d" % i,
        is_active=False) for i in range(10))).execute()

    PeerReviewExternalId.insert_many((dict(
        peer_review_record=PeerReviewRecord.get(id=1),
        type="Test1_%d" % i,
        value="Test1_%d" % i,
        url="Test1_%d" % i,
        relationship="Test1_%d" % i) for i in range(10))).execute()

    PeerReviewInvitee.insert_many((dict(
        peer_review_record=PeerReviewRecord.get(id=1),
        orcid="1231123112311%d" % i,
        first_name="Test1_%d" % i,
        last_name="Test1_%d" % i,
        put_code=i,
        status="Test1_%d" % i,
        identifier="1%d" % i,
        visibility = "PUBLIC",
        email="Test1_%d" % i) for i in range(10))).execute()

    WorkRecord.insert_many((dict(
        task=Task.get(id=1),
        title="Test_%d" % i,
        sub_title="Test_%d" % i,
        translated_title="Test_%d" % i,
        translated_title_language_code="Test_%d" % i,
        journal_title="Test_%d" % i,
        short_description="Test_%d" % i,
        citation_type="Test_%d" % i,
        citation_value="Test_%d" % i,
        type="Test_%d" % i,
        url="Test_%d" % i,
        language_code="Test_%d" % i,
        country="Test_%d" % i,
        is_active=False,
        status="Test_%d" % i) for i in range(10))).execute()

    WorkContributor.insert_many((dict(
        work_record=WorkRecord.get(id=1),
        orcid="123112311231%d" % i,
        name="Test_%d" % i,
        contributor_sequence="%d" % i,
        role="Test_%d" % i) for i in range(10))).execute()

    WorkExternalId.insert_many((dict(
        work_record=WorkRecord.get(id=1),
        type="Test_%d" % i,
        value="Test_%d" % i,
        url="Test_%d" % i,
        relationship="Test_%d" % i) for i in range(10))).execute()

    WorkInvitee.insert_many((dict(
        work_record=WorkRecord.get(id=1),
        orcid="123112311231%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        put_code=i,
        status="Test_%d" % i,
        identifier="%d" % i,
        visibility="Test_%d" % i,
        email="Test_%d" % i) for i in range(10))).execute()

    yield testdb


def test_user_uuid():
    u = User(email="test@gtest.com")
    assert str(u.uuid) == "8428e5f6-38c6-530f-8339-9aeffb99e022"


def test_user_org_link_user_constraint(models):
    org = Organisation.get(id=1)
    uo = UserOrg(user_id=999999, org=org)
    with pytest.raises(User.DoesNotExist):
        uo.save()


def test_user_org_link_org_constraint(models):
    user = User.select().limit(1).first()
    from peewee import IntegrityError
    with pytest.raises(IntegrityError):
        UserOrg.create(user=user, org_id=999999)


def test_test_database(models):
    """Test of the consitency of the test database."""
    assert Organisation.select().count() == 10
    assert User.select().count() == 63
    assert OrcidToken.select().count() == 60
    assert AffiliationRecord.select().count() == 10
    assert FundingRecord.select().count() == 10
    assert FundingContributor.select().count() == 10
    assert FundingInvitee.select().count() == 10
    assert ExternalId.select().count() == 10
    assert WorkRecord.select().count() == 10
    assert WorkContributor.select().count() == 10
    assert WorkExternalId.select().count() == 10
    assert WorkInvitee.select().count() == 10
    assert PeerReviewRecord.select().count() == 10
    assert PeerReviewExternalId.select().count() == 10
    assert PeerReviewInvitee.select().count() == 10
    assert ResearcherUrlRecord.select().count() == 10
    assert OtherNameRecord.select().count() == 10
    assert Task.select().count() == 30
    assert UserOrgAffiliation.select().count() == 30

    assert User.get(id=43).admin_for.count() == 10
    assert User.get(id=1).admin_for.count() == 0
    assert User.get(id=42).admin_for.count() > 0
    assert User.get(id=2).organisations.count() > 0
    assert Organisation.get(id=1).admins.count() == 1
    assert Organisation.get(id=5).users.count() > 0
    assert Organisation.get(id=5).admins.count() > 0
    assert User.select().where(User.orcid == User.get(
        email="user_the_same_id_0@org0.org.nz").orcid).count() == 3
    assert len(User.get(email="user_the_same_id_0@org0.org.nz").org_links) == 3

    user = User.get(email="user0@org0.org.nz")
    available_organisations = user.available_organisations
    assert available_organisations.count() == 10

    admin = User.create(email="admin@org0.org.nz", organisation=user.organisation, confirmed=True,
            first_name="TEST", last_name="ADMIN", roles=Role.ADMIN)
    ui = UserInvitation.create(email=user.email, invitee=user, inviter=admin, token="TOKEN-123")
    admin.delete_instance()
    ui = UserInvitation.get(ui.id)
    assert ui.inviter_id is None
    user.delete_instance()
    assert not UserInvitation.select().where(UserInvitation.id == ui.id).exists()

    org = Organisation.select().limit(1).first()
    user = User.select().limit(1).first()
    ot = OrcidToken.create(user=user, org=org, scope="S1,S2,S3")
    assert len(ot.scopes) == 3

    ot.scopes = ["A", "B", "C", "D"]
    assert ot.scope == "A,B,C,D"


def test_roles():
    assert Role.RESEARCHER == "RESEARCHER"
    assert Role.RESEARCHER == Role["RESEARCHER"]
    assert Role.RESEARCHER != "ADMIN"
    assert Role.RESEARCHER != Role["ADMIN"]
    assert hash(Role.RESEARCHER) == hash("RESEARCHER")


def test_user_roles(models):
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


def test_admin_is_admin(models):
    user = User(
        name="Test User ABC123",
        first_name="ABC",
        last_name="123",
        email="user_abc_123@org.org.nz",
        confirmed=True,
        roles=Role.ADMIN | Role.RESEARCHER)

    assert user.is_admin


def test_drop_tables(models):
    drop_tables()
    assert not User.table_exists()
    assert not Organisation.table_exists()
    assert not UserOrg.table_exists()


def test_create_tables(models):
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


def test_task_type_field():

    db = SqliteDatabase(":memory:")

    class TestModel(Model):
        tt = TaskTypeField(null=True)

        class Meta:
            database = db

    TestModel.create_table()
    TestModel.create(tt=None)
    for v in TaskType:
        TestModel.create(tt=v)
        TestModel.create(tt=str(v.value))
        TestModel.create(tt=v.value)
        TestModel.create(tt=v.name)
    TestModel.create(tt=dict())
    res = {r[0]:r[1] for r in db.execute_sql(
        "SELECT tt, count(*) AS rc FROM testmodel GROUP BY tt ORDER BY 1").fetchall()}
    assert all(res[v.value] == 4 for v in TaskType)
    assert res[None] == 2


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


def test_load_org_info_from_csv(models):
    # flake8: noqa
    OrgInfo.load_from_csv(
        """Organisation,Title,First Name,Last Name,Role,Email,Phone,Permission to post to web,Country Code,City of home campus,common:disambiguated-organization-identifier,common:disambiguation-source
Organisation_0,Title_0,First Name_0,Last Name_0,Role_0,Email_0,Phone_0,Permission to post to web_0,Country Code_0,City of home campus_0,common:disambiguated-organization-identifier_0,common:disambiguation-source
Organisation_1,Title_1,First Name_1,Last Name_1,Role_1,Email_1,Phone_1,yes,Country Code_1,City of home campus_1,common:disambiguated-organization-identifier_1,common:disambiguation-source
""")
    assert OrgInfo.select().count() == 2
    oi = OrgInfo.get(name="Organisation_1")
    assert oi.is_public

    OrgInfo.load_from_csv(
        StringIO("""Name,Disambiguated Id,Disambiguation Source
AgResearch Ltd,3713,RINGGOLD
Aqualinc Research Ltd,9429035717133,NZBN
Ara Institute of Canterbury,6006,Education Organisation Number
Auckland District Health Board,1387,RINGGOLD
Auckland University of Technology,1410,RINGGOLD
Bay of Plenty District Health Board,7854,RINGGOLD
Capital and Coast District Health Board,8458,RINGGOLD
Cawthron Institute,5732,RINGGOLD
CRL Energy Ltd,9429038654381,NZBN

Health Research Council,http://dx.doi.org/10.13039/501100001505,FUNDREF
Hutt Valley District Health Board,161292,RINGGOLD
Institute of Environmental Science and Research,8480,RINGGOLD
Institute of Geological & Nuclear Sciences Ltd,5180,RINGGOLD
"""))
    assert OrgInfo.select().count() == 15


def test_affiliations(models):
    assert Affiliation.EDU == "EDU"
    assert Affiliation.EMP == "EMP"
    assert Affiliation.EMP == Affiliation["EMP"]
    assert hash(Affiliation.EMP) == hash("EMP")
    assert str(Affiliation.EDU | Affiliation.EMP) == "Education, Employment"


def test_field_is_updated(testdb):
    u = User.create(email="test@test.com", name="TESTER")
    u.save()
    u.save()
    assert not u.field_is_updated("name")
    u.name = "NEW VALUE"
    assert u.field_is_updated("name")


def test_load_task_from_csv(models):
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


def test_work_task(models):
    org = Organisation.select().first()
    raw_data0 = open(os.path.join(os.path.dirname(__file__), "data", "example_works.json"), "r").read()
    data0 = load_yaml_json("test0001.json", raw_data0)
    assert isinstance(data0, list) and isinstance(data0[0], NestedDict)
    data0 = load_yaml_json(None, source=raw_data0, content_type="json")
    assert isinstance(data0, list) and isinstance(data0[0], NestedDict)
    data0 = load_yaml_json(None, source=raw_data0)
    assert isinstance(data0, list) and isinstance(data0[0], NestedDict)
    task0 = WorkRecord.load_from_json(filename="work0042.json", source=raw_data0, org=org)
    data = task0.to_export_dict()
    raw_data = json.dumps(data, cls=JSONEncoder)
    task = WorkRecord.load_from_json(filename="work0001.json", source=raw_data, org=org)
    export = task.to_export_dict()
    for a in ["id", "filename", "created-at", "updated-at"]:
        del(export[a])
        del(data[a])
    assert data == export


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
    db = SqliteDatabase(":memory:")

    class TestTable(BaseModel):
        test_field = TextField()

        class Meta:
            database = db

    class Child(BaseModel):
        parent = ForeignKeyField(TestTable)

        class Meta:
            database = db

    TestTable.create_table()
    Child.create_table()

    parent = TestTable.create(test_field="ABC123")

    assert parent.to_dict() == {"id": 1, "test_field": "ABC123"}

    child = Child.create(parent=parent)
    parent = TestTable.get(parent.id)
    assert parent.to_dict(backrefs=True) == {"id": 1, "test_field": "ABC123", "child_set": [{"id": 1}]}

    rec = TestTable.get(1)
    assert rec.test_field == "ABC123"

    rec = TestTable.get()
    assert rec.test_field == "ABC123"
