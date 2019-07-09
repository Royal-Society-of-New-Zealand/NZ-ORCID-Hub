*** Settings ***
Documentation       Test if can open the ORCIDHub and read 'About' and 'FAQ'
Library             SeleniumLibrary     run_on_failure=Nothing
Test Setup          Open Browser & Set Speed
Test Teardown       Close Browser
Variables           resources/variables.py
# Resource            resources/resource.robot
# Resource            resources/tuakiri/login.robot
# Resource            resources/tuakiri/uoa.robot
# Resource            resources/organisation.robot

*** Variables ***

*** Test Cases ***
Anonymous user can access 'About' page
    Open Browser    ${URL}/about   browser=${BROWSER}

*** Keywords ***
Open Browser & Set Speed
    Open Browser    ${URL}   browser=${BROWSER}
    Set Selenium Speed  ${DELAY}
