# -*- coding: utf-8 -*-
"""Application module gluing script.

Simple solution to overcome circular import problem:
http://charlesleifer.com/blog/structuring-flask-apps-a-how-to-for-those-coming-from-django/
"""

import logging
import os

import click

import models  # noqa: F401
from api import *  # noqa: F401,F403
from application import app
from authcontroller import *  # noqa: F401,F403
from oauth import *  # noqa: F401,F403
from reports import *  # noqa: F401,F403
from utils import process_affiliation_records, process_funding_records
from views import *  # noqa: F401,F403


@app.before_first_request
def setup_logging():
    """Set-up logger to log to STDOUT (eventually conainer log)."""
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(logging.INFO)


@app.cli.command()
@click.option("-d", "--drop", is_flag=True, help="Drop tables before creating...")
@click.option("-f", "--force", is_flag=True, help="Enforce table craeation.")
@click.option("-A", "--audit", is_flag=True, help="Create adit trail tables.")
@click.option(
    "-V",
    "--verbose",
    is_flag=True,
    help="Shows SQL statements that get sent to the server or DB.")
def initdb(create=False, drop=False, force=False, audit=True, verbose=False):
    """Initialize the database."""
    if drop and force:
        models.drop_tables()

    if verbose:
        logger = logging.getLogger("peewee")
        if logger:
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())

    try:
        models.create_tables()
    except Exception:
        app.logger.exception("Failed to create tables...")

    if audit:
        app.logger.info("Creating audit tables...")
        models.create_audit_tables()

    super_user, created = models.User.get_or_create(
        email="root@mailinator.com", roles=models.Role.SUPERUSER)

    if not created:
        return

    super_user.name = "The University of Auckland"
    super_user.confirmed = True
    super_user.save()

    org, _ = models.Organisation.get_or_create(
        name="The University of Auckland", tuakiri_name="University of Auckland", confirmed=True)


@app.cli.group()
@click.option("-v", "--verbose", is_flag=True)
def load(verbose):
    """Load data from files."""
    app.verbose = verbose


@load.command()
@click.argument('input', type=click.File('r'), required=True)
def org_info(input):
    """Pre-loads organisation data."""
    row_count = models.OrgInfo.load_from_csv(input)
    click.echo(f"Loaded {row_count} records")


@app.cli.command()
@click.option("-n", default=20, help="Max number of rows to process.")
def process(n):
    """Process uploaded affiliation and funding records."""
    process_affiliation_records(n)
    process_funding_records(n)


if os.environ.get("ENV") == "dev0":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.debug = True

if app.debug:
    from flask_debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)
    # logger = logging.getLogger('peewee')
    # logger.setLevel(logging.DEBUG)
    # logger.addHandler(logging.StreamHandler())

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ["ENV"] = "dev0"
    app.debug = True
    app.secret_key = os.urandom(24)
    app.run(debug=True, port=8000)
