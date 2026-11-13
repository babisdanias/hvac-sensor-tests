*** Settings ***
Documentation     Temperature unit setting.
Resource          resources/common.resource
Test Setup        Reset Device


*** Test Cases ***
Default Unit Is Celsius
    [Tags]    smoke
    Command Should Return    UNIT    C
    ${reading}=    Get Reading
    Should Be Equal    ${reading}[unit]    C

Switching To Fahrenheit Converts The Reading
    Command Should Return    TEST ENV T 25    OK
    Command Should Return    UNIT F    OK
    ${reading}=    Get Reading
    Should Be Equal    ${reading}[unit]    F
    # 25 C = 77 F, allow for sensor noise
    Reading Should Be Within    T    76.5    77.5

Switching Back To Celsius
    Command Should Return    UNIT F    OK
    Command Should Return    UNIT C    OK
    Reading Should Be Within    T    21    23

Invalid Unit Is Rejected And Setting Is Kept
    Command Should Return    UNIT K    ERR 03 INVALID VALUE
    Command Should Return    UNIT    C

Reset Restores Celsius
    Command Should Return    UNIT F    OK
    Command Should Return    RESET    OK
    Command Should Return    UNIT    C
