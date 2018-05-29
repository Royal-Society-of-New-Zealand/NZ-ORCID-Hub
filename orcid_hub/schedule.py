# -*- coding: utf-8 -*-
"""Various utilities."""

from orcid_hub import utils as tasks
from datetime import timedelta

tasks.process_tasks.schedule(timedelta(hours=1))
