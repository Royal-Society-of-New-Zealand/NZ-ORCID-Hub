from os import environ

SERVER = 'dev.orcidhub.org.nz'
BROWSER = 'Chrome'
# BROWSER = 'phantomjs'
DELAY = 0.1
LOGIN_URL = 'https://' + SERVER + '/Tuakiri/login'
ONBOARD_URL = 'https://' + SERVER + '/invite/organisation'
ORG_ADMIN_URL = 'https://' + SERVER + '/admin/organisation'

TEST_USERNAME = environ.get('TEST_USERNAME')
TEST_PASSWORD = environ.get('TEST_PASSWORD')

UOA_IDP = 'http://iam.test.auckland.ac.nz/idp'
UOA_FORM_NAME = '_eventId_proceed'

ORGANISATION = '0000 TEST ORGANISATION'
ORGANISATION_EMAIL = 'researcher.23232zzdfdf@mailinator.com'