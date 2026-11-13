*** Settings ***
Documentation     The device tells us what it is.
Resource          resources/common.resource
Test Setup        Reset Device
Test Tags         smoke


*** Test Cases ***
Device Reports Model And Firmware
    Command Should Return    VERS    HVS-100 1.2.0

Serial Number Has Expected Format
    ${serial}=    Send Command    SNUM
    Should Match Regexp    ${serial}    ^[A-Z]\\d{7}$

Help Lists The Main Commands
    ${help}=    Send Command    HELP
    FOR    ${cmd}    IN    VERS    SEND    STATUS    UNIT    ALARM    RESET
        Should Contain    ${help}    ${cmd}
    END

Healthy Device Reports OK Status
    Command Should Return    STATUS    OK
