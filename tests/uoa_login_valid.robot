*** Settings ***
Documentation     A test suite with a single test for valid login.
...
...               This test has a workflow that is created using keywords in
...               the imported resource file.
Suite Setup       Open Browser To UOA Login Page
Suite Teardown    Close Browser
Test Setup        University of Auckland Login Page
Resource          resources/resource.robot
Resource          resources/uoa_login.robot
Variables         resources/config.py

*** Variables ***
${UOA USERNAME}     ${TEST_USERNAME}
${UOA PASSWORD}     ${TEST_PASSWORD}


*** Test Cases ***
Valid Login
    Login UoA       ${UOA USERNAME}     ${UOA_PASSWORD}
    Onboard Organisation Should Be Open