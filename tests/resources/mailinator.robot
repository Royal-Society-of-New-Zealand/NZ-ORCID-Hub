*** Settings ***
Documentation     Mailinator Service Resource File
Library           SeleniumLibrary   run_on_failure=Nothing
Library           String
Resource          resource.robot
Variables         variables.py

*** Keywords ***
Go To Mailinator Inbox
    [Arguments]     ${email}
    ${email} =      Fetch From Left     ${email}    @
    ${url} =        Set Variable    ${MAILINATOR_START_URL}${email}${MAILINATOR_END_URL}
    Go To       ${url}

Open Newest Email
    Click Element       //div[@title="FROM"]

OrcidHub Email
    ${heading}

Orcid Email
    ${heading} =    //div[@id=]

# Deactivate Orcid Account
    # Select Frame    xpath=(//iframe[@id='msg_body']|//frame[@id='msg_body'])
    # Click Link      https://sandbox.orcid.org/account/confirm-deactivate-orcid
    # # Click Link      xpath=(a[contains(@href,'confirm-deactivate-orcid')])
    # # Click Link      a[@href='http://click1.clickrouter.com/redirect?token=a2258079c24c4c50a56b6b1ffb75d6e2&url=https%3A//sandbox.orcid.org/account/confirm-deactivate-orcid/bnFnLzFVSDQ4RURZa3c5YXlENVVQZWVZU2J0Um5OUVdleVEvU1pYS2ZUamR2eFFrNytZUWljZlhta2g3aUJ4YVNLNFVYRHQ5cHFYV09qQ3hSMndMeFE9PQ%3Flang%3Den')]
    # # Click Link      xpath=(//body/div/p[1]/a[2])
    # Pause Execution