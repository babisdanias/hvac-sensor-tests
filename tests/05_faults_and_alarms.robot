*** Settings ***
Documentation     Sensor faults, out-of-range conditions and the CO2 alarm.
Resource          resources/common.resource
Test Setup        Reset Device


*** Test Cases ***
Broken Humidity Sensor Is Reported
    Command Should Return    TEST FAULT RH    OK
    ${reading}=    Get Reading
    Should Be Equal    ${reading}[RH]    ${None}
    Command Should Return    STATUS    ERR RH SENSOR

Other Sensors Keep Working When One Fails
    Command Should Return    TEST FAULT RH    OK
    Reading Should Be Within    T      21    23
    Reading Should Be Within    CO2    580   620

Fault Clears
    Command Should Return    TEST FAULT CO2    OK
    Command Should Return    TEST CLEAR    OK
    Command Should Return    STATUS    OK

Temperature Above Range Saturates And Is Flagged
    [Documentation]    Sensor range is -40..60 C. At 75 C it should report 60 and flag it.
    Command Should Return    TEST ENV T 75    OK
    ${reading}=    Get Reading
    Should Be Equal As Numbers    ${reading}[T]    60.0
    Command Should Return    STATUS    ERR T OUT OF RANGE

CO2 Alarm Triggers Above Threshold
    [Tags]    smoke
    Command Should Return    ALARM CO2 1000    OK
    Command Should Return    TEST ENV CO2 1200    OK
    Command Should Return    STATUS    ALARM CO2

No Alarm Below Threshold
    Command Should Return    TEST ENV CO2 900    OK
    Command Should Return    STATUS    OK

No Alarm At Exactly The Threshold
    [Documentation]    Boundary value: the alarm fires above the threshold, not at it.
    Command Should Return    ALARM CO2 1000    OK
    Command Should Return    TEST ENV CO2 1000    OK
    Command Should Return    STATUS    OK

Alarm Threshold Can Be Changed
    Command Should Return    ALARM CO2 1500    OK
    Command Should Return    ALARM    CO2 1500
    Command Should Return    TEST ENV CO2 1200    OK
    Command Should Return    STATUS    OK

Invalid Alarm Thresholds Are Rejected
    [Template]    Alarm Value Should Be Rejected
    0
    -5
    6000
    abc


*** Keywords ***
Alarm Value Should Be Rejected
    [Arguments]    ${value}
    Command Should Return    ALARM CO2 ${value}    ERR 03 INVALID VALUE
    Command Should Return    ALARM    CO2 1000
