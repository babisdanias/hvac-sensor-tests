*** Settings ***
Documentation     Readings are sane, stable, and follow the environment.
Resource          resources/common.resource
Test Setup        Reset Device


*** Test Cases ***
Default Readings Are In A Normal Room Range
    [Tags]    smoke
    Reading Should Be Within    T      21    23
    Reading Should Be Within    RH     43    47
    Reading Should Be Within    CO2    580   620

Readings Are Stable Over Time
    [Documentation]    Ten readings in a row should not jump more than the sensor noise.
    ${first}=    Get Reading
    FOR    ${i}    IN RANGE    10
        ${next}=    Get Reading
        ${diff}=    Evaluate    abs(${next}[T] - ${first}[T])
        Should Be True    ${diff} <= 0.5    T jumped by ${diff}
    END

Device Follows Environment Change
    [Documentation]    Data-driven: each row is one test with different values.
    [Template]    Reading Should Follow Environment
    # quantity    set to    low       high
    T             30        29.5      30.5
    T             -10       -10.5     -9.5
    RH            80        79        81
    RH            10        9         11
    CO2           1500      1490      1510


*** Keywords ***
Reading Should Follow Environment
    [Arguments]    ${quantity}    ${value}    ${low}    ${high}
    Command Should Return    TEST ENV ${quantity} ${value}    OK
    Reading Should Be Within    ${quantity}    ${low}    ${high}
