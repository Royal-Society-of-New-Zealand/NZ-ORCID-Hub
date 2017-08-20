*** Settings ***
Documentation     A test suite with a single test for valid login.
...
...               This test has a workflow that is created using keywords in
...               the imported resource file.
Resource          resource.robot
Variables           Password.py

*** Variables ***
${UOA USERNAME}     djim087
${UOA PASSWORD}     ${PASSWORD}

*** Test Cases ***
Valid Login
    Open Browser To Login Page
    Select Identity Provider    ${UOA IDP}
    University of Auckland Login
    Input Username              ${UOA USERNAME}
    Input Password              ${UOA PASSWORD}
    Submit Credentials  ${UOA FORM NAME}
    University of Auckland Information Release
    Onboard Organisation Should Be Open
    [Teardown]    Close Browser

Invalid Login
    Open Browser To Login Page
    Select Identity Provider    ${UOA IDP}
    Input Username              John
    Input Password              Doe
    Submit Credentials  ${UOA FORM NAME}
    University of Auckland Login
    [Teardown]    Close Browser