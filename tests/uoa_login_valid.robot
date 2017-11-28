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
Resource          resources/organisation.robot
Variables         resources/variables.py

*** Test Cases ***
Valid Login
    Login UoA       ${TEST_USERNAME}     ${TEST_PASSWORD}
    Onboard Organisation Should Be Open