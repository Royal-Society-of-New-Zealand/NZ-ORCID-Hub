# -*- coding: utf-8 -*-
"""Tests for batch processing."""
from datetime import datetime
import os
from unittest.mock import Mock, patch
from io import BytesIO

import pytest
from flask_login import login_user
from peewee import Model, SqliteDatabase

from utils import get_profile, get_resources, readup_test_data
from orcid_hub import utils
from orcid_hub.models import *


data_path = os.path.join(os.path.dirname(__file__), "data")


def test_process_task_from_csv_with_failures(request_ctx):
    """Test task loading and processing with failures."""
    org = Organisation.get(name="TEST0")
    super_user = User.get(email="admin@test0.edu")
    with patch("emails.html") as mock_msg, request_ctx("/") as ctx:
        login_user(super_user)
        # flake8: noqa
        task = AffiliationRecord.load_from_csv(
            """First name	Last name	email address	Organisation	Campus/Department	City	Course or Job title	Start date	End date	Student/Staff
    FNA	LBA	admin@test0.edu	TEST1	Research Funding	Wellington	Programme Manager - ORCID	2016-09		Staff
    """,
            filename="TEST.tsv",
            org=org,
        )
        AffiliationRecord.update(is_active=True).where(
            AffiliationRecord.task_id == task.id
        ).execute()
        mock_msg().send = Mock(side_effect=Exception("FAILED TO SEND EMAIL"))
        utils.process_affiliation_records(10000)
        rec = AffiliationRecord.select().where(AffiliationRecord.task_id == task.id).first()
        assert "FAILED TO SEND EMAIL" in rec.status
        assert rec.processed_at is not None


def test_upload_affiliation_with_wrong_country(request_ctx, mocker):
    """Test task loading and processing with failures."""
    org = Organisation.get(name="TEST0")
    super_user = User.get(email="admin@test0.edu")
    with request_ctx("/") as ctx:
        exception = mocker.patch.object(ctx.app.logger, "exception")
        login_user(super_user)
        # flake8: noqa
        with pytest.raises(ModelExceptionError):
            task = AffiliationRecord.load_from_csv(
                """First name\tLast name\temail address\tOrganisation\tCampus/Department\tCity\tCourse or Job title\tStart date\tEnd date\tStudent/Staff\tCountry
FNA\tLBA\taaa.lnb@test.com\tTEST1\tResearch Funding\tWellington\tProgramme Manager - ORCID\t2016-09 19:00:00 PM\t\tStaff\tNO COUNTRY
        """,
                filename="TEST.tsv",
                org=org,
            )

        # this should work:
        task = AffiliationRecord.load_from_csv(
            """First name\tLast name\temail address\tOrganisation\tCampus/Department\tCity\tCourse or Job title\tStart date\tEnd date\tStudent/Staff\tCountry
FNA\tLBA\taaa.lnb@test.com\tTEST1\tResearch Funding\tWellington\tProgramme Manager - ORCID\t2016-09 19:00:00 PM\t\tStaff\t
    """,
            filename="TEST-2.tsv",
            org=org,
        )
        rec = task.records.first()
        assert rec.country is None
    exception.assert_called_once()


def test_process_tasks(client, mocker):
    """Test expiration data setting and deletion of the exprired tasks."""
    org = Organisation.get(name="TEST0")
    admin = User.get(email="admin@test0.edu")
    send_email = mocker.patch("orcid_hub.utils.send_email")
    client.login(admin)

    # flake8: noqa
    task = AffiliationRecord.load_from_csv(
        """First name	Last name	email address	Organisation	Campus/Department	City	Course or Job title\tStart date	End date	Student/Staff\tCountry
FNA	LBA	aaa.lnb123@test.com	TEST1	Research Funding	Wellington	Programme Manager - ORCID	2016-09		Staff\tNew Zealand
""",
        filename="TEST_TASK.tsv",
        org=org,
    )
    Task.update(created_at=datetime(1999, 1, 1), updated_at=datetime(1999, 1, 1)).execute()
    utils.process_tasks()
    assert Task.select().count() == 1
    assert not Task.select().where(Task.expires_at.is_null()).exists()
    send_email.assert_called_once()
    task = Task.select().first()
    args, kwargs = send_email.call_args
    assert "email/task_expiration.html" in args
    assert kwargs["error_count"] == 0

    assert kwargs["export_url"].endswith(f"/admin/affiliationrecord/export/csv/?task_id={task.id}")
    assert kwargs["recipient"] == (admin.name, admin.email,)
    assert kwargs["subject"] == "Batch process task is about to expire"
    assert kwargs["task"] == task

    # After the second go everything should be deleted
    utils.process_tasks()
    assert Task.select().count() == 0

    # Funding processing task:
    task = Task.create(
        created_at=datetime(1999, 1, 1),
        org=org,
        filename="FUNDING.json",
        created_by=admin,
        updated_by=admin,
        task_type=TaskType.FUNDING,
    )

    Task.update(updated_at=datetime(1999, 1, 1)).execute()
    assert Task.select().where(Task.expires_at.is_null()).count() == 1

    utils.process_tasks()
    assert Task.select().count() == 1
    assert Task.select().where(Task.expires_at.is_null()).count() == 0

    utils.process_tasks()
    assert Task.select().count() == 0
    args, kwargs = send_email.call_args
    assert "email/task_expiration.html" in args
    assert kwargs["error_count"] == 0
    assert kwargs["export_url"].endswith(f"/admin/fundingrecord/export/csv/?task_id={task.id}")
    assert kwargs["recipient"] == (admin.name, admin.email,)
    assert kwargs["subject"] == "Batch process task is about to expire"
    assert kwargs["task"] == task

    # Incorrect task type:
    task = Task.create(
        created_at=datetime(1999, 1, 1),
        org=org,
        filename="ERROR.err",
        created_by=admin,
        updated_by=admin,
        task_type=-12345,
    )

    Task.update(updated_at=datetime(1999, 1, 1)).execute()
    with patch("orcid_hub.app.logger.error") as error:
        utils.process_tasks()
        error.assert_called_with('Unknown task "ERROR.err" (ID: 1) task type.')
    task.delete().execute()

    # Cover case with an exterenal SP:
    with patch("orcid_hub.utils.EXTERNAL_SP", "SOME.EXTERNAL.SP"):
        Task.create(
            created_at=datetime(1999, 1, 1),
            org=org,
            filename="FILE.file",
            created_by=admin,
            updated_by=admin,
        )
        Task.update(updated_at=datetime(1999, 1, 1)).execute()
        assert Task.select().count() == 1
        utils.process_tasks()
        utils.process_tasks()
        assert Task.select().count() == 0


def test_enqueue_user_records(client, mocker):
    """Test user related record enqueing."""

    mocker.patch("orcid_hub.utils.send_email")

    raw_data = readup_test_data("example_works.json", "r")

    user = (
        User.select().join(OrcidToken, on=OrcidToken.user).where(User.orcid.is_null(False)).first()
    )
    org = user.organisation
    admin = org.admins.first()
    client.login(admin)

    task = WorkRecord.load_from_json(raw_data, filename="works.json", org=org)
    WorkInvitee.update(email=user.email, orcid=user.orcid).execute()
    WorkRecord.update(is_active=True).execute()

    record_ids = [r.id for r in task.records]
    get_record = mocker.patch("orcid_hub.orcid_client.MemberAPIV3.get_record", get_profile)
    create_or_update_work = mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.create_or_update_work",
        return_value=(123, user.orcid, True, "PUBLIC"),
    )
    utils.process_work_records(record_id=record_ids)

    raw_data = readup_test_data("example_peer_reviews.json", "r")
    task = PeerReviewRecord.load_from_json(raw_data, filename="example_peer_reviews.json", org=org)
    PeerReviewRecord.update(is_active=True).execute()
    PeerReviewInvitee.update(email=user.email, orcid=user.orcid).execute()

    create_or_update_affiliation = mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.create_or_update_affiliation",
        return_value=(321, user.orcid, True, "PUBLIC"),
    )
    task = Task.create(org=org, task_type=TaskType.AFFILIATION, filename="affiliations.csv")
    AffiliationRecord.insert_many(
        dict(
            task_id=task.id,
            is_active=True,
            email=user.email,
            orcid=user.orcid,
            affiliation_type="student" if i % 2 else "staff",
            organisation=org.name,
            role=f"ROLE #{i}",
        )
        for i in range(1, 100)
    ).execute()
    utils.enqueue_user_records(user)
    create_or_update_work.assert_called()
    create_or_update_affiliation.assert_called()


def test_email_logging(client, mocker):
    """Test if the log entry gets crated."""

    org = Organisation.get()
    client.application.config["SERVER_NAME"] = "ordidhub.org"
    client.login_root()

    with app.app_context():
        send = mocker.patch(
            "emails.message.Message.send", return_value=Mock(success=True, message="All Good!")
        )
        utils.send_email(
            "email/test.html",
            recipient="test@test.ac.nz",
            sender=("SENDER", "sender@test.ac.nz"),
            subject="TEST ABC 123",
        )
        send.assert_called()
        assert MailLog.select().where(MailLog.was_sent_successfully).exists()

        send = mocker.patch(
            "emails.message.Message.send", return_value=Mock(success=False, message="ERROR!")
        )
        with pytest.raises(Exception):
            utils.send_email(
                "email/test.html",
                recipient="test@test.ac.nz",
                sender=("SENDER", "sender@test.ac.nz"),
                subject="TEST ABC 123",
            )
        send.assert_called()
        assert MailLog.select().where(MailLog.was_sent_successfully.NOT()).exists()

        resp = client.get("/admin/maillog/")
        assert resp.status_code == 200

        for r in MailLog.select():
            resp = client.get(f"/admin/maillog/details/?id={r.id}&url=%2Fadmin%2Fmaillog%2F")
            assert resp.status_code == 200


def test_message_records(client, mocker):
    """Test message records processing."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)

    raw_data0 = readup_test_data("resources.json")
    resp = client.post(
        "/load/task/RESOURCE",
        data={"file_": (BytesIO(raw_data0), "resources.json")},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"SYN-18-UOA-333" in resp.data
    assert b"SYN-18-UOA-222" in resp.data
    # assert b"bob42@mailinator.com" in resp.data
    # assert b"alice42@mailinator.com" in resp.data
    task = Task.get(filename="resources.json")
    assert task.records.count() == 2

    send = mocker.patch("emails.message.MessageSendMixin.send")
    get_resources_mock = mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.get_resources",
        return_value=get_resources(org=user.organisation, user=user),
    )
    execute = mocker.patch("orcid_hub.orcid_client.MemberAPIV3.execute")

    resp = client.post("/activate_all/?url=/resources", data=dict(task_id=task.id))
    assert resp.status_code == 302
    assert resp.location.endswith("/resources")

    get_resources_mock.assert_called()
    execute.assert_called()

    send.assert_called()
    assert UserInvitation.select().count() == 3

    # via task view - activate all:
    UserInvitation.delete().execute()
    MessageRecord.update(is_active=False).execute()

    resp = client.post("/admin/task/action/", data=dict(action="activate", rowid=[task.id]))
    assert resp.status_code == 302
    assert resp.location.endswith("/admin/task/")
    assert UserInvitation.select().count() == 3

    # via task view - reset all:
    UserInvitation.delete().execute()
    resp = client.post("/admin/task/action/", data=dict(action="reset", rowid=[task.id]))
    assert resp.status_code == 302
    assert resp.location.endswith("/admin/task/")
    assert UserInvitation.select().count() == 3

    # Edit invitees
    for r in task.records:
        for i in r.invitees:
            resp = client.get(f"/admin/invitee/details/?id={i.id}")
            resp = client.post(
                f"/admin/invitee/edit/?id={i.id}&url=/admin/invitee/%2F%3Frecord_id={r.id}",
                data=dict(
                    identifier=f"ID-{i.id}",
                    # email="researcher@test0.edu",
                    first_name=i.first_name or "FN",
                    last_name=i.first_name or "LN",
                    visibility="limited",
                ),
                follow_redirects=True,
            )
            resp = client.get(f"/admin/invitee/details/?id={i.id}")
            invitee = Invitee.get(i.id)
            assert invitee.identifier == f"ID-{i.id}"

        invitee_count = r.invitees.count()
        resp = client.post(
            f"/admin/invitee/new/?url=/admin/invitee/%2F%3Frecord_id={r.id}",
            data=dict(
                email="a-new-one@org1234.edu",
                first_name="FN",
                last_name="LN",
                visibility="limited",
            ),
        )
        assert r.invitees.count() == invitee_count + 1

    # Export and re-import
    for export_type in ["json", "yaml"]:
        resp = client.get(f"/admin/messagerecord/export/{export_type}/?task_id={task.id}")
        data = json.loads(resp.data) if export_type == "json" else yaml.load(resp.data)
        data0 = data.copy()
        del data0["id"]

        file_name = f"resources_reimport.{export_type}"
        resp = client.post(
            "/load/task/RESOURCE",
            data={
                "file_": (
                    BytesIO(
                        (json.dumps(data0) if export_type == "json" else yaml.dump(data0)).encode()
                    ),
                    file_name,
                )
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"SYN-18-UOA-333" in resp.data
        assert b"SYN-18-UOA-222" in resp.data

        t = Task.get(filename=file_name)
        assert t.records.count() == 2
        assert t.is_raw

        # with the the existing ID
        resp = client.post(
            "/load/task/RESOURCE",
            data={
                "file_": (
                    BytesIO(
                        (json.dumps(data) if export_type == "json" else yaml.dump(data)).encode()
                    ),
                    file_name,
                )
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"SYN-18-UOA-333" in resp.data
        assert b"SYN-18-UOA-222" in resp.data

        t = Task.get(filename=file_name)
        assert t.records.count() == 2
        assert t.is_raw


def test_message_records_completed(client, mocker):
    """Test message records processing with handling the complition of the task."""
    admin = client.data["admin"]
    user = OrcidToken.select().join(User).where(User.orcid.is_null(False)).first().user
    org = user.organisation
    mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.get_resources",
        return_value=get_resources(org=user.organisation, user=user),
    )
    send = mocker.patch("emails.message.MessageSendMixin.send")
    execute = mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.execute",
        return_value=Mock(
            headers={"Location": f"{user.orcid}/ABC/123456"}, json=dict(visibility="public")
        ),
    )
    task = Task.create(
        is_active=True,
        created_by=admin,
        filename="messages.json",
        task_type=TaskType.RESOURCE,
        is_raw=True,
        org=org,
    )
    record = MessageRecord.create(task=task, message="{}", is_active=True)
    invitee = Invitee.create(email=user.email, orcid=user.orcid)
    record.invitees.add(invitee)
    record.save()
    utils.process_message_records(record_id=record.id)
    send.assert_called_once()

    MessageRecord.update(processed_at=None).execute()
    Invitee.update(processed_at=None).execute()
    send_email = mocker.patch("orcid_hub.utils.send_email")
    utils.process_message_records(record_id=record.id)
    send_email.assert_called_once()
    args, _ = send_email.call_args
    assert args[0] == "email/task_completed.html"
    assert Task.get(task.id).completed_at is not None


def test_affiliation_records(client, mocker):
    """Test affiliation records processing."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)

    with open(os.path.join(data_path, "affiliations.csv"), "rb") as f:
        resp = client.post(
            "/load/task/AFFILIATION",
            data={"file_": (f, "affiliations.csv")},
            follow_redirects=True,
        )
    assert resp.status_code == 200
    assert b"55561720" in resp.data
    assert b"208013283/01" in resp.data
    task = Task.get(filename="affiliations.csv")
    assert task.records.count() == 4

    send = mocker.patch("emails.message.MessageSendMixin.send")
    mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.get_record",
        lambda s: get_profile(org=s.org, user=s.user),
    )
    urlopen = mocker.patch(
        "urllib3.poolmanager.PoolManager.urlopen",
        return_value=Mock(status_code=201, headers={"Location: /record/424242"}),
    )

    resp = client.post("/activate_all/?url=/affiliations", data=dict(task_id=task.id))
    assert resp.status_code == 302
    assert resp.location.endswith("/affiliations")

    urlopen.assert_called()
    for (args, kwargs) in urlopen.call_args_lis:
        assert args[0] == "PUT"

    send.assert_called()
    assert UserInvitation.select().count() == 1

    resp = client.get(f"/admin/affiliationrecord/?task_id={task.id}")
    assert b"555" in resp.data
