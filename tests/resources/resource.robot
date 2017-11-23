*** Settings ***
Documentation     A resource file with reusable keywords and variables.
...
...               The system specific keywords created here form our own
...               domain specific language. They utilize keywords provided
...               by the imported Selenium2Library.
Library           SeleniumLibrary

*** Variables ***
${SERVER}               dev.orcidhub.org.nz
<<<<<<< HEAD:tests/resources/resource.robot
${BROWSER}              phantomjs
${DELAY}                0.1
${LOGIN URL}            https://${SERVER}/Tuakiri/login
${ONBOARD URL}          https://${SERVER}/invite/organisation
=======
${BROWSER}              Chrome
${DELAY}                0.1
${LOGIN URL}            https://${SERVER}/Tuakiri/login
${ONBOARD URL}          https://${SERVER}/invite/organisation
${ORG ADMIN URL}        https://${SERVER}/admin/organisation/
>>>>>>> 9deba0db520f12a7cd6bcfe8725bfd25e29fd994:tests/resources/resource.robot

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
    Select From List By Value  //select[@name="FedSelector"]  Tuakiri TEST Federation
    Select From List By Value  //select[@name="origin"]  ${provider}
    Submit Form     IdPList

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

Onboard an Organisation
    [Arguments]  ${organisation}    ${organisation_email}
    Go To               ${ONBOARD URL}
    Input Text      name=org_name   ${organisation}
    Input Text      name=org_email  ${organisation email}
    Submit Form