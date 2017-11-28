*** Settings ***
Documentation     University of Auckland Login Resource File.
Library           SeleniumLibrary   run_on_failure=Nothing
Variables         variables.py

*** Keywords ***
Login UoA
    [Arguments]    ${username}      ${password}
    Input Username                  ${username}
    Input Password                  ${password}
    Submit Credentials              ${UOA_FORM_NAME}
    University of Auckland Information Release

Open Browser To UOA Login Page
    Open Browser To Login Page
    Select Identity Provider    ${UOA_IDP}

University of Auckland Login Page
    Title Should Be    The University of Auckland Login Servic

University of Auckland Information Release
    ${title}    Get Title
    Run Keyword If  '${title}' == 'Information Release'   Click Button    name=_eventId_proceed
