# -*- coding: utf-8 -*-
"""Various utilities."""

from orcid_hub import utils as tasks
from datetime import timedelta

tasks.process_tasks.schedule(timedelta(seconds=5), interval=3600, repeat=2)
