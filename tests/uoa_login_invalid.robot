*** Settings ***
Documentation             A test suite with a single test for invalid login.
Test Setup                Open Browser & Set Speed
Test Teardown            Close Browser
Resource                  resources/resource.robot
Test Template             Login With Invalid Credentials Should Fail
Resource                  resources/tuakiri/login.robot
Resource                  resources/tuakiri/uoa.robot
Variables                 resources/variables.py

*** Test Cases ***
Invalid Username                 invalid          ${TEST_PASSWORD}
Invalid Password                 ${TEST_USERNAME}  invalid
Invalid Username And Password    invalid          whatever
Empty Username                   ${EMPTY}         ${TEST_PASSWORD}
Empty Password                   ${TEST_USERNAME}  ${EMPTY}
Empty Username And Password      ${EMPTY}         ${EMPTY}

*** Keywords ***
Login With Invalid Credentials Should Fail
    [Arguments]    ${username}      ${password}
    Login UoA   ${username}     ${password}
    University of Auckland Login Page