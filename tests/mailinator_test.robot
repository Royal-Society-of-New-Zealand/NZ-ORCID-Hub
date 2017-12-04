*** Settings ***
Documentation       Mailinator Tests.
Test Setup          Open Browser & Set Speed
Test Teardown       Close Browser
Resource            resources/mailinator.robot
Resource            resources/resource.robot

*** Test Case ***
Newest Email Test
    Go To Mailinator Inbox  ${TEST_EMAIL}
    Open Newest Email
    Deactivate Orcid Account
