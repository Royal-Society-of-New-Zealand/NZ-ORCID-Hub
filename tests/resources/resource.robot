*** Settings ***
Documentation       A resource file with reusable keywords and variables.
...
...                 The system specific keywords created here form our own
...                 domain specific language. They utilize keywords provided
...                 by the imported Selenium2Library.
Library             SeleniumLibrary     run_on_failure=Nothing
Variables           variables.py

*** Keywords ***
Open Browser & Set Speed
    Open Browser    ${URL}   browser=${BROWSER}
    Set Selenium Speed  ${DELAY}