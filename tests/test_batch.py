# -*- coding: utf-8 -*-
"""Tests for batch processing."""
from unittest.mock import Mock, patch

import pytest
from flask_login import login_user
from peewee import Model, SqliteDatabase
from playhouse.test_utils import test_database

from orcid_hub import utils
from orcid_hub.models import (Affiliation, AffiliationRecord, ModelException, OrcidToken,
                              Organisation, OrgInfo, PartialDate, PartialDateField, Role, Task,
                              User, UserOrg, UserOrgAffiliation, create_tables, drop_tables)


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
