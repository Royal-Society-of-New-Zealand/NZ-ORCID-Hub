*** Settings ***
Documentation     Orcid Sandbox Resource File
Library           SeleniumLibrary   run_on_failure=Nothing
Variables         ../variables.py

*** Keywords ***
Go To Orcid
    Go To       ${ORCID_URL}

Signin to Orcid
    [Arguments]     ${user}         ${pass}
    Input Text    //input[@name="userId"]    ${ORCID_USER}
    Input Text    //input[@name="password"]  ${TEST_PASSWORD}