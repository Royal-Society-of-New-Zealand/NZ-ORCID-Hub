import models
from models import Organisation, Role, User


def initdb():
    """Creates the database."""

    models.drop_tables()
    models.create_tables()

    super_user = User(
        name="The University of Auckland", email="root@mailinator.com", confirmed=True, roles=Role.SUPERUSER)
    super_user.save()

    org1 = Organisation(
        name="The University of Auckland",
        email="root@mailinator.com",
        tuakiri_name="University of Auckland")
    org1.save()

if __name__ == "__main__":
    initdb()
