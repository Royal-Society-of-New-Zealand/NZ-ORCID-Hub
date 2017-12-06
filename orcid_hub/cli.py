"""This is a management script for the ORCID Hub application."""
import click
from flask.cli import FlaskGroup

# from . import app


# @click.group(cls=FlaskGroup, create_app=lambda *args, **kwargs: app)
@click.group(cls=FlaskGroup)
def cli():
    """Run the management script for the ORCID Hub application."""
    pass


def main():
    """Run the management script for the ORCID Hub application."""
    cli()


if __name__ == '__main__':
    main()
