*** Settings ***
Documentation     A resource file with reusable keywords and variables.
...
...               The system specific keywords created here form our own
...               domain specific language. They utilize keywords provided
...               by the imported Selenium2Library.
Library           Selenium2Library

*** Variables ***
${SERVER}           dev.orcidhub.org.nz
${BROWSER}          Chrome
${DELAY}            0.1
${LOGIN URL}        https://${SERVER}/Tuakiri/login
${ONBOARD URL}      https://${SERVER}/invite/organisation

*** Variables ***
#${TUAKIRI FED}      Tuakiri New Zealand Access Federation
${UOA IDP}          http://iam.auckland.ac.nz/idp
${UOA FORM NAME}      _eventId_proceed

*** Keywords ***
Open Browser To Login Page
    Open Browser    ${LOGIN URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Login Page Should Be Open

Login Page Should Be Open
    Title Should Be    Select your Home Organisation

Go To Login Page
    Go To    ${LOGIN URL}
    Login Page Should Be Open

Select Identity Provider
    [Arguments]     ${provider}
    #Select From List By Value   name=FedSelector ${federation}
    Select From List By Value   name=origin  ${provider}
    Submit Form     IdPList

University of Auckland Login
    Title Should Be    The University of Auckland Login Service

University of Auckland Information Release
    ${title}    Get Title
    Run Keyword If  '${title}' == 'Information Release'   Click Button    name=_eventId_proceed

# Most identity providers use a username and password field with the following ids.
Input Username
    [Arguments]    ${username}
    Input Text    id=username    ${username}

Input Password
    [Arguments]    ${password}
    Input Text    id=password    ${password}

Submit Credentials
    [Arguments]     ${name}
    # Submit the first form on the page.
    Click Button   name=${name}

Onboard Organisation Should Be Open
    Location Should Be      ${ONBOARD URL}
    Title Should Be         New Zealand ORCID Hub
