*** Settings ***
Documentation             A test suite with a single test for valid login.
Test Setup                Open Browser & Set Speed
Test Teardown             Close Browser
Resource                  resources/resource.robot
Resource                  resources/tuakiri/login.robot
Resource                  resources/tuakiri/uoa.robot
Resource                  resources/organisation.robot

*** Test Cases ***
Valid Login
    Login UoA       ${TEST_USERNAME}     ${TEST_PASSWORD}
    Onboard Organisation Should Be Open