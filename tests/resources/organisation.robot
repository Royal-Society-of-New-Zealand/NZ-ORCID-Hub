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