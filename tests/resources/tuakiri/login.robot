*** Settings ***
Documentation     Generic Federated Tuakiri Login
Library           SeleniumLibrary   run_on_failure=Nothing
Variables         ../variables.py

*** Keywords ***
Login Page Should Be Open
    Title Should Be     Select your Home Organisation

Go To Login Page
    Go To    ${LOGIN_URL}
    Login Page Should Be Open

Select Identity Provider
    [Arguments]     ${provider}
    Select From List By Value   //select[@name='FedSelector']   Tuakiri TEST Federation
    Select From List By Value   //select[@name='origin']        ${provider}
    Submit Form     IdPList

# Most identity providers use a username and password field with the following ids.
Input Username
    [Arguments]     ${username}
    Input Text      //input[@id='username']     ${username}

Input Password
    [Arguments]     ${password}
    Input Text      //input[@id='password']     ${password}

Submit Credentials
    [Arguments]     ${name}
    # Submit the first form on the page.
    Click Button    //button[@name='${name}']