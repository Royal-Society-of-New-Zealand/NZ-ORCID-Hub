# -*- coding: utf-8 -*-
"""Various utilities."""

from . import utils as tasks, rq
from datetime import datetime


def setup():
    """Set up the application schedule. Remove any already scheduled jobs."""
    scheduler = rq.get_scheduler()
    for job in scheduler.get_jobs():
        job.delete()

    # NB! add result_ttl! Otherwise it won't get rescheduled
    tasks.process_tasks.schedule(datetime.utcnow(), interval=3600, result_ttl=-1, job_id="*PROCESS-TASKS*")
    tasks.send_orcid_update_summary.cron("0 0 1 * *", "*ORCID-UPDATE-SUMMARY*")
