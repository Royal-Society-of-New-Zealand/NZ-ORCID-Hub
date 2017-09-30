*** Settings ***
Documentation     A test suite with a single test for invalid login.
Suite Setup       Open Browser To UOA Login Page
Suite Teardown    Close Browser
Test Setup        University of Auckland Login Page
Test Template     Login With Invalid Credentials Should Fail
Resource          resources/resource.robot
Resource          resources/uoa_login.robot
Variables         resources/config.py


*** Variables ***
${UOA USERNAME}     ${TEST_USERNAME}
${UOA PASSWORD}     ${TEST_PASSWORD}

*** Test Cases ***
Invalid Username                 invalid          ${UOA PASSWORD}
Invalid Password                 ${UOA USERNAME}  invalid
Invalid Username And Password    invalid          whatever
Empty Username                   ${EMPTY}         ${UOA PASSWORD}
Empty Password                   ${UOA USERNAME}  ${EMPTY}
Empty Username And Password      ${EMPTY}         ${EMPTY}

*** Keywords ***
Login With Invalid Credentials Should Fail
    [Arguments]    ${username}      ${password}
    Login UoA   ${username}     ${password}
    University of Auckland Login Page