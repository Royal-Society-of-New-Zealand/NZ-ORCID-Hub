*** Settings ***
Documentation       Organisation Onboarding Tests.
Test Setup          Open Browser & Set Speed
Test Teardown       Close Browser
Library             String
# Library             FakerLibrary
Resource            resources/organisation.robot
Resource            resources/tuakiri/login.robot
Resource            resources/tuakiri/uoa.robot
Resource            resources/resource.robot



*** Test Cases ***
Onboard & Remove Organisation
    Login UoA       ${TEST_USERNAME}     ${TEST_PASSWORD}
    Onboard an Organisation     ${ORGANISATION}     ${ORGANISATION_EMAIL}
    Remove Organisation  ${ORGANISATION}

Onboard Organisation
    Login UoA       ${TEST_USERNAME}     ${TEST_PASSWORD}
    Onboard an Organisation     ${ORGANISATION}     ${ORGANISATION_EMAIL}
    Find Organisation       ${ORGANISATION}
    Edit Organisation       ${ORGANISATION}
    Input Text          //input[@name="orcid_client_id"]    ${ORGANISATION_ORCID_CLIENT_ID}
    Input Text          //input[@name="orcid_secret"]    ${ORGANISATION_ORCID_SECRET}
    Click Element       //input[@id='confirmed']
    Click Button        //input[@value='Save']