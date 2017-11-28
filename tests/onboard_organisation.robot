*** Settings ***
Documentation       Organisation Onboarding Tests.
...
...                 This test has a workflow that is created using keywords in
...                 the imported resource file.
Suite Setup         Open Browser To UOA Login Page
Suite Teardown      Close Browser
Resource            resources/resource.robot
Resource            resources/organisation.robot
Resource            resources/uoa_login.robot
Variables           resources/variables.py

*** Test Cases ***
Onboard Organisation
    Login UoA       ${TEST_USERNAME}     ${TEST_PASSWORD}
    Onboard an Organisation     ${ORGANISATION}     ${ORGANISATION_EMAIL}
    
# Remove Organisation
#     Login UoA       ${UOA USERNAME}     ${UOA_PASSWORD}
#     Onboard an Organisation     ${ORGANISATION}     ${ORGANISATION EMAIL}
#     Click Link    //a[@title="Sort by Name"]
