"""Conviguration for the testing."""
from os import environ

TEST_USERNAME = environ.get("TEST_USERNAME", "rad42@mailinator.com")
PASSWORD = environ.get("PASSWORD", "p455w0rd")
