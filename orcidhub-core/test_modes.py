import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest import TestCase, main
from models import User, Organisation, UserOrg, Role
from playhouse.test_utils import test_database
from peewee import SqliteDatabase
from itertools import product

_db = SqliteDatabase(':memory:')


class ModelTestCase(TestCase):

    def create_test_data(self):
        Organisation.insert_many((dict(
            name="Organisation #%d" % i,
            email="admin@org%d.org.nz" % i,
            tuakiri_name="Organisation #%d" % i,
            orcid_client_id="client-%d" % i,
            orcid_secret="secret-%d" % i,
            confirmed=(i % 2 == 0))
            for i in range(1000))).execute()

        User.insert_many((dict(
            name="Test User #%d" % i,
            first_name="Test_%d" % i,
            last_name="User_%d" % i,
            email="user%d@org%d.org.nz" % (i, i * 42 % 1000),
            edu_person_shared_token="EDU PERSON SHARED TOKEN #%d" % i,
            confirmed=(i % 3 != 0),
            roles=Role.SUPERUSER if i % 42 == 0 else Role.ADMIN if i % 13 == 0 else Role.RESEARCHER)
            for i in range(6000))).execute()

        UserOrg.insert_many((dict(
            is_admin=((u + o) % 23 == 0),
            user=u,
            org=o) for (u, o) in product(range(2, 6000, 43), range(2, 1000, 3)))).execute()

        UserOrg.insert_many((dict(
            is_admin=True,
            user=42,
            org=o) for o in range(1, 1001))).execute()

    def test_user_org_link(self):
        with test_database(_db, (User, Organisation, UserOrg,)):
            self.create_test_data()
            assert User.select().count() == 6000
            assert Organisation.select().count() == 1000
            assert User.get(id=42).admin_for.count() == 1000
            assert User.get(id=1).admin_for.count() == 0
            assert User.get(id=45).admin_for.count() > 0
            assert User.get(id=2).organisations.count() > 0
            assert Organisation.get(id=1).admins.count() == 1
            assert Organisation.get(id=5).users.count() > 0
            assert Organisation.get(id=5).admins.count() > 0


if __name__ == '__main__':
    main()
