import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application import app
import unittest


class OrcidhubTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def login(self, username, password):
        pass

    def test_index(self):
        rv = self.app.get("/")
        assert b"<!DOCTYPE html>" in rv.data
        assert b"Home" in rv.data
        assert b"Royal Society of New Zealand" in rv.data, \
            "'Royal Society of New Zealand' should be present on the index page."

    def test_auth(self):
        pass


if __name__ == '__main__':
    unittest.main()
