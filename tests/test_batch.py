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
from orcid_api_v3.rest import ApiException

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
            org=org)
        AffiliationRecord.update(is_active=True).where(
            AffiliationRecord.task_id == task.id).execute()
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
        with pytest.raises(ModelException):
            task = AffiliationRecord.load_from_csv(
                """First name\tLast name\temail address\tOrganisation\tCampus/Department\tCity\tCourse or Job title\tStart date\tEnd date\tStudent/Staff\tCountry
FNA\tLBA\taaa.lnb@test.com\tTEST1\tResearch Funding\tWellington\tProgramme Manager - ORCID\t2016-09 19:00:00 PM\t\tStaff\tNO COUNTRY
        """,
                filename="TEST.tsv",
                org=org)

        # this should work:
        task = AffiliationRecord.load_from_csv(
            """First name\tLast name\temail address\tOrganisation\tCampus/Department\tCity\tCourse or Job title\tStart date\tEnd date\tStudent/Staff\tCountry
FNA\tLBA\taaa.lnb@test.com\tTEST1\tResearch Funding\tWellington\tProgramme Manager - ORCID\t2016-09 19:00:00 PM\t\tStaff\t
    """,
            filename="TEST-2.tsv",
            org=org)
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
        org=org)
    Task.update(created_at=datetime(1999, 1, 1), updated_at=datetime(1999, 1, 1)).execute()
    utils.process_tasks()
    assert Task.select().count() == 1
    assert not Task.select().where(Task.expires_at.is_null()).exists()
    send_email.assert_called_once()
    task = Task.select().first()
    args, kwargs = send_email.call_args
    assert "email/task_expiration.html" in args
    assert kwargs["error_count"] == 0

    assert kwargs["export_url"].endswith(
        f"/admin/affiliationrecord/export/csv/?task_id={task.id}")
    assert kwargs["recipient"] == (
        admin.name,
        admin.email,
    )
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
        task_type=TaskType.FUNDING)

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
    assert kwargs["export_url"].endswith(
        f"/admin/fundingrecord/export/csv/?task_id={task.id}")
    assert kwargs["recipient"] == (
        admin.name,
        admin.email,
    )
    assert kwargs["subject"] == "Batch process task is about to expire"
    assert kwargs["task"] == task

    # Incorrect task type:
    task = Task.create(
        created_at=datetime(1999, 1, 1),
        org=org,
        filename="ERROR.err",
        created_by=admin,
        updated_by=admin,
        task_type=-12345)

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
            updated_by=admin)
        Task.update(updated_at=datetime(1999, 1, 1)).execute()
        assert Task.select().count() == 1
        utils.process_tasks()
        utils.process_tasks()
        assert Task.select().count() == 0


def test_enqueue_user_records(client, mocker):
    """Test user related record enqueing."""

    mocker.patch("orcid_hub.utils.send_email")

    raw_data =  readup_test_data("example_works.json", "r")

    user = User.select().join(OrcidToken, on=OrcidToken.user).where(User.orcid.is_null(False)).first()
    org = user.organisation
    admin = org.admins.first()
    client.login(admin)

    task = WorkRecord.load_from_json(raw_data, filename="works.json", org=org)
    WorkInvitee.update(email=user.email, orcid=user.orcid).execute()
    WorkRecord.update(is_active=True).execute()

    raw_data =  readup_test_data("example_peer_reviews.json", "r")
    task = PeerReviewRecord.load_from_json(raw_data, filename="example_peer_reviews.json", org=org)
    PeerReviewRecord.update(is_active=True).execute()
    PeerReviewInvitee.update(email=user.email, orcid=user.orcid).execute()

    get_record = mocker.patch("orcid_hub.orcid_client.MemberAPIV3.get_record", get_profile)
    create_or_update_work = mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.create_or_update_work",
        return_value=(123, user.orcid, True, "PUBLIC"))
    create_or_update_affiliation = mocker.patch(
        "orcid_hub.orcid_client.MemberAPIV3.create_or_update_affiliation",
        return_value=(321, user.orcid, True, "PUBLIC"))
    task = Task.create(org=org, task_type=TaskType.AFFILIATION, filename="affiliations.csv")
    AffiliationRecord.insert_many(
        dict(task_id=task.id,
             is_active=True,
             email=user.email,
             orcid=user.orcid,
             affiliation_type="student" if i % 2 else "staff",
             organisation=org.name,
             role=f"ROLE #{i}") for i in range(1, 100)).execute()
    utils.enqueue_user_records(user)
    create_or_update_work.assert_called()
    create_or_update_affiliation.assert_called()


def test_email_logging(client, mocker):
    """Test if the log entry gets crated."""

    org = Organisation.get()
    client.application.config["SERVER_NAME"] = "ordidhub.org"
    client.login_root()

    with app.app_context():
        send = mocker.patch("emails.message.Message.send",
                            return_value=Mock(success=True, message="All Good!"))
        utils.send_email("email/test.html",
                        recipient="test@test.ac.nz",
                        sender=("SENDER", "sender@test.ac.nz"),
                        subject="TEST ABC 123")
        send.assert_called()
        assert MailLog.select().where(MailLog.was_sent_successfully).exists()


        send = mocker.patch("emails.message.Message.send",
                            return_value=Mock(success=False, message="ERROR!"))
        with pytest.raises(Exception):
            utils.send_email("email/test.html",
                            recipient="test@test.ac.nz",
                            sender=("SENDER", "sender@test.ac.nz"),
                            subject="TEST ABC 123")
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
        follow_redirects=True)
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
        return_value=get_resources(org=user.organisation, user=user))
    execute = mocker.patch("orcid_hub.orcid_client.MemberAPIV3.execute")

    resp = client.post("/activate_all/?url=/resources", data=dict(task_id=task.id))
    assert resp.status_code == 302
    assert resp.location.endswith("/resources")

    get_resources_mock.assert_called()
    execute.assert_called()

    send.assert_called()
    assert UserInvitation.select().count() == 2


