# -*- coding: utf-8 -*-
"""Tests for batch processing."""
from datetime import datetime
import os
from unittest.mock import Mock, patch

import pytest
from flask_login import login_user
from peewee import Model, SqliteDatabase
from playhouse.test_utils import test_database

from orcid_hub import utils
from orcid_hub.models import *

def test_process_task_from_csv_with_failures(request_ctx):
    """Test task loading and processing with failures."""
    org = Organisation.get(name="TEST0")
    super_user = User.get(email="admin@test0.edu")
    with patch("emails.html") as mock_msg, request_ctx("/") as ctx:
        login_user(super_user)
        # flake8: noqa
        task = Task.load_from_csv(
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
            task = Task.load_from_csv(
                """First name\tLast name\temail address\tOrganisation\tCampus/Department\tCity\tCourse or Job title\tStart date\tEnd date\tStudent/Staff\tCountry
FNA\tLBA\taaa.lnb@test.com\tTEST1\tResearch Funding\tWellington\tProgramme Manager - ORCID\t2016-09 19:00:00 PM\t\tStaff\tNO COUNTRY
        """,
                filename="TEST.tsv",
                org=org)

        # this should work:
        task = Task.load_from_csv(
            """First name\tLast name\temail address\tOrganisation\tCampus/Department\tCity\tCourse or Job title\tStart date\tEnd date\tStudent/Staff\tCountry
FNA\tLBA\taaa.lnb@test.com\tTEST1\tResearch Funding\tWellington\tProgramme Manager - ORCID\t2016-09 19:00:00 PM\t\tStaff\t
    """,
            filename="TEST-2.tsv",
            org=org)
        rec = task.records.first()
        assert rec.country is None
    exception.assert_called_once()


def test_process_tasks(request_ctx):
    """Test expiration data setting and deletion of the exprired tasks."""
    org = Organisation.get(name="TEST0")
    super_user = User.get(email="admin@test0.edu")
    with patch("orcid_hub.utils.send_email") as send_email, request_ctx("/") as ctx:
        login_user(super_user)
        # flake8: noqa
        task = Task.load_from_csv(
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
        hostname = ctx.request.host
        assert kwargs["export_url"].endswith(
            f"//{hostname}/admin/affiliationrecord/export/csv/?task_id={task.id}")
        assert kwargs["recipient"] == (
            super_user.name,
            super_user.email,
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
            created_by=super_user,
            updated_by=super_user,
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
        hostname = ctx.request.host
        assert kwargs["export_url"].endswith(
            f"//{hostname}/admin/fundingrecord/export/csv/?task_id={task.id}")
        assert kwargs["recipient"] == (
            super_user.name,
            super_user.email,
        )
        assert kwargs["subject"] == "Batch process task is about to expire"
        assert kwargs["task"] == task

        # Incorrect task type:
        task = Task.create(
            created_at=datetime(1999, 1, 1),
            org=org,
            filename="ERROR.err",
            created_by=super_user,
            updated_by=super_user,
            task_type=-12345)

        Task.update(updated_at=datetime(1999, 1, 1)).execute()
        with pytest.raises(Exception, message="Unexpeced task type: -12345 (ERROR.err)."):
            utils.process_tasks()
        task.delete().execute()

        # Cover case with an exterenal SP:
        with patch("orcid_hub.utils.EXTERNAL_SP", "SOME.EXTERNAL.SP"):
            Task.create(
                created_at=datetime(1999, 1, 1),
                org=org,
                filename="FILE.file",
                created_by=super_user,
                updated_by=super_user)
            Task.update(updated_at=datetime(1999, 1, 1)).execute()
            assert Task.select().count() == 1
            utils.process_tasks()
            utils.process_tasks()
            assert Task.select().count() == 0


def test_enqueue_user_records(client, mocker):
    """Test user related record enqueing."""

    mocker.patch("orcid_hub.utils.send_email")
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    raw_data = open(os.path.join(data_dir, "example_works.json"), "r").read()

    user = User.select().join(OrcidToken).where(User.orcid.is_null(False)).first()
    org = user.organisation
    admin = org.admins.first()
    client.login(admin)

    task = WorkRecord.load_from_json(raw_data, filename="works.json", org=org)
    WorkInvitee.update(email=user.email, orcid=user.orcid).execute()
    WorkRecord.update(is_active=True).execute()

    raw_data = open(os.path.join(data_dir, "example_peer_reviews.json"), "r").read()
    task = PeerReviewRecord.load_from_json(raw_data, filename="example_peer_reviews.json", org=org)
    PeerReviewRecord.update(is_active=True).execute()
    PeerReviewInvitee.update(email=user.email, orcid=user.orcid).execute()

    task = Task.create(org=org, task_type=TaskType.AFFILIATION, filename="affiliations.csv")
    AffiliationRecord.insert_many(
        dict(task_id=task.id,
             is_active=True,
             email=user.email,
             orcid=user.orcid,
             affiliation_type="student" if i % 2 else "staff",
             organisation=org.name,
             role=f"ROLE #{i}") for i in range(1, 100))

    utils.enqueue_user_records(user)
