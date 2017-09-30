*** Settings ***
Documentation     A resource file for University of Auckland Login.
Library           SeleniumLibrary

*** Variables ***
${UOA IDP}              http://iam.test.auckland.ac.nz/idp
${UOA FORM NAME}        _eventId_proceed

*** Keywords ***
Login UoA
    [Arguments]    ${username}      ${password}
    Input Username                  ${username}
    Input Password                  ${password}
    Submit Credentials              ${UOA FORM NAME}
    University of Auckland Information Release

Open Browser To UOA Login Page
    Open Browser To Login Page
    Select Identity Provider    ${UOA IDP}

University of Auckland Login Page
    Title Should Be    The University of Auckland Login Service

University of Auckland Information Release
    ${title}    Get Title
    Run Keyword If  '${title}' == 'Information Release'   Click Button    name=_eventId_proceed
