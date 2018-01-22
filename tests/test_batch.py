# -*- coding: utf-8 -*-
"""Tests for batch processing."""
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from flask_login import login_user
from peewee import Model, SqliteDatabase
from playhouse.test_utils import test_database

from orcid_hub import utils
from orcid_hub.models import (Affiliation, AffiliationRecord, ModelException, OrcidToken,
                              Organisation, OrgInfo, PartialDate, PartialDateField, Role, Task,
                              TaskType, User, UserOrg, UserOrgAffiliation, create_tables,
                              drop_tables)


def test_load_task_from_csv_with_failures(request_ctx):
    org = Organisation.create(name="TEST0", tuakiri_name="TEST")
    super_user = User.create(
        email="admin@test.edu",
        name="TEST",
        first_name="FIRST_NAME",
        last_name="LAST_NAME",
        confirmed=True,
        is_superuser=True,
        organisation=org)
    with patch("emails.html") as mock_msg, request_ctx("/") as ctx:
        login_user(super_user)
        # flake8: noqa
        task = Task.load_from_csv(
            """First name	Last name	email address	Organisation	Campus/Department	City	Course or Job title	Start date	End date	Student/Staff
    FNA	LBA	aaa.lnb@test.com	TEST1	Research Funding	Wellington	Programme Manager - ORCID	2016-09		Staff
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


def test_process_tasks(request_ctx):
    """Test expiration data setting and deletion of the exprired tasks."""
    org = Organisation.create(name="TEST0", tuakiri_name="TEST")
    super_user = User.create(
        email="admin@test.edu",
        name="TEST",
        first_name="FIRST_NAME",
        last_name="LAST_NAME",
        confirmed=True,
        is_superuser=True,
        organisation=org)
    with patch("orcid_hub.utils.send_email") as send_email, request_ctx("/") as ctx:
        login_user(super_user)
        # flake8: noqa
        task = Task.load_from_csv(
            """First name	Last name	email address	Organisation	Campus/Department	City	Course or Job title	Start date	End date	Student/Staff
    FNA	LBA	aaa.lnb123@test.com	TEST1	Research Funding	Wellington	Programme Manager - ORCID	2016-09		Staff
    """,
            filename="TEST_TASK.tsv",
            org=org)
        Task.update(created_at=datetime(1999, 1, 1)).execute()
        utils.process_tasks()
        assert Task.select().count() == 1
        assert not Task.select().where(Task.expires_at.is_null()).exists()
        send_email.assert_called_once()
        task = Task.select().first()
        args, kwargs = send_email.call_args
        assert "email/task_expiration.html" in args
        assert kwargs["error_count"] == 0
        hostname = ctx.request.host
        assert kwargs["export_url"] == (
            f"https://{hostname}/admin/affiliationrecord/export/csv/?task_id={task.id}")
        assert kwargs["recipient"] == ("TEST", "admin@test.edu", )
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
            task_type=TaskType.FUNDING.value)

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
        assert kwargs["export_url"] == (
            f"https://{hostname}/admin/fundingrecord/export/csv/?task_id={task.id}")
        assert kwargs["recipient"] == ("TEST", "admin@test.edu", )
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
            assert Task.select().count() == 1
            utils.process_tasks()
            utils.process_tasks()
            assert Task.select().count() == 0

