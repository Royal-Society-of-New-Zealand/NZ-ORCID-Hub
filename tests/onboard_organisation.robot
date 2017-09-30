*** Settings ***
Documentation     A test suite with a single test for valid login.
...
...               This test has a workflow that is created using keywords in
...               the imported resource file.
Suite Setup       Open Browser To UOA Login Page
Suite Teardown    Close Browser
Resource          resources/resource.robot
Resource          resources/uoa_login.robot
Variables         resources/config.py

*** Variables ***
${UOA USERNAME}     ${TEST_USERNAME}
${UOA PASSWORD}     ${TEST_PASSWORD}
${ORGANISATION}         Sancta Maria College
${ORGANISATION EMAIL}   daniel.jimenez@auckland.ac.nz

*** Test Cases ***
Onboard Organisation
    Login UoA       ${UOA USERNAME}     ${UOA_PASSWORD}
    Onboard an Organisation     ${ORGANISATION}     ${ORGANISATION EMAIL}
    
#Remove Organisation
    #Login UoA       ${UOA USERNAME}     ${UOA_PASSWORD}
    #Onboard an Organisation     ${ORGANISATION}     ${ORGANISATION EMAIL}
