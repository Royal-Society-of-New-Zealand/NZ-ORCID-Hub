*** Settings ***
Documentation       A resource file with reusable keywords and variables.
...
...                 The system specific keywords created here form our own
...                 domain specific language. They utilize keywords provided
...                 by the imported Selenium2Library.
Library             SeleniumLibrary     run_on_failure=Nothing
Variables           variables.py

*** Keywords ***
Open Browser To Login Page
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed  ${DELAY}
    Login Page Should Be Open

Login Page Should Be Open
    Title Should Be     Select your Home Organisation

Go To Login Page
    Go To    ${LOGIN_URL}
    Login Page Should Be Open

Select Identity Provider
    [Arguments]     ${provider}
    Select From List By Value   //select[@name="FedSelector"]   Tuakiri TEST Federation
    Select From List By Value   //select[@name="origin"]        ${provider}
    Submit Form     IdPList

# Most identity providers use a username and password field with the following ids.
Input Username
    [Arguments]     ${username}
    Input Text      id=username     ${username}

Input Password
    [Arguments]     ${password}
    Input Text      id=password     ${password}

Submit Credentials
    [Arguments]     ${name}
    # Submit the first form on the page.
    Click Button    name=${name}