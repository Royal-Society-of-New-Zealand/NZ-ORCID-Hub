from os import environ

SERVER = 'dev.orcidhub.org.nz'
BROWSER = environ.get('BROWSER', 'phantomjs')
DELAY = 0.1
URL = 'https://' + SERVER
LOGIN_URL = 'https://' + SERVER + '/Tuakiri/login'
ONBOARD_URL = 'https://' + SERVER + '/invite/organisation'
ORG_ADMIN_URL = 'https://' + SERVER + '/admin/organisation'

TEST_USERNAME = environ.get('TEST_USERNAME')
TEST_PASSWORD = environ.get('TEST_PASSWORD')

UOA_IDP = 'http://iam.test.auckland.ac.nz/idp'
UOA_FORM_NAME = '_eventId_proceed'

ORGANISATION = '0000 TEST ORGANISATION'
ORGANISATION_EMAIL = 'researcher.23232zzdfdf@mailinator.com'
ORGANISATION_ORCID_CLIENT_ID = 'APP-5ZVH4JRQ0C27RVH5'
ORGANISATION_ORCID_SECRET = environ.get('ORGANISATION_ORCID_SECRET', '1234')

ORCID_URL = 'https://sandbox.orcid.org/signin'
ORCID_USER = 'orcidtestmailuser@mailinator.com'

MAILINATOR_START_URL = 'https://www.mailinator.com/v2/inbox.jsp?zone=public&query='
MAILINATOR_END_URL = '#/#inboxpane'

TEST_EMAIL = 'orcidtestmailuser@mailinator.com'


