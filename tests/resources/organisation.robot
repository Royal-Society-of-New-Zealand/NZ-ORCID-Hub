*** Settings ***
Documentation       A resource file with reusable keywords and variables.
...
...                 The system specific keywords created here form our own
...                 domain specific language. They utilize keywords provided
...                 by the imported Selenium2Library.
Library             SeleniumLibrary     run_on_failure=Nothing
Variables           variables.py

*** Keywords ***
Onboard Organisation Should Be Open
    Location Should Be      ${ONBOARD_URL}
    Title Should Be     New Zealand ORCID Hub

Onboard an Organisation
    [Arguments]     ${organisation}     ${organisation_email}
    Go To           ${ONBOARD_URL}
    Input Text      //input[@name="org_name"]       ${organisation}
    Input Text      //input[@name="org_email"]      ${organisation email}
    Click Element   //input[@name="tech_contact"]
    Submit Form

Find Organisation
    [Arguments]     ${org}
    Go To           ${ORG_ADMIN_URL}
    Input Text      //input[@name='search']     ${org}
    Press Key       //input[@name='search']     \\13
    Click Link      //a[@title="Sort by Name"]

Remove Organisation
    [Arguments]     ${org_to_remove}
    Find Organisation   ${org_to_remove}
    Click Link      xpath=(//td[text()[contains(.,'${org_to_remove}')]]/parent::*/td[@class='list-buttons-column']/a)
    ${org} =        Get Value   //input[@name="name"]
    ${href} =       Get Location
    ${result} =     Fetch From Right    ${href}     id=
    ${id} =         Fetch From Left     ${result}   &
    Should Be Equal     '${org}'    '${org_to_remove}'
    Find Organisation   ${org}
    Choose Ok On Next Confirmation
    Click Button    xpath=(//input[@value='${id}']/parent::*/button)
    Confirm Action