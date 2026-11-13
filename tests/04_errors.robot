*** Settings ***
Documentation     Bad input gets a clear error, and the device keeps working.
Resource          resources/common.resource
Test Setup        Reset Device


*** Test Cases ***
Unknown Command Is Rejected
    Command Should Return    FOO    ERR 01 UNKNOWN COMMAND

Empty Line Is A Syntax Error
    Command Should Return    ${EMPTY}    ERR 02 SYNTAX

Commands Are Not Case Sensitive
    Command Should Return    vers    HVS-100 1.2.0
    Command Should Return    Unit    C

Extra Arguments To SEND Are Rejected
    Command Should Return    SEND NOW    ERR 02 SYNTAX

Device Still Works After Bad Commands
    [Tags]    smoke
    FOR    ${bad}    IN    FOO    UNIT X    ALARM CO2 abc    TEST
        ${answer}=    Send Command    ${bad}
        Should Start With    ${answer}    ERR
    END
    Command Should Return    STATUS    OK
    Reading Should Be Within    T    21    23
