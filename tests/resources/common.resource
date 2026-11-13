*** Settings ***
Documentation     Shared setup: start the simulator, connect, reset between tests.
Library           Process
Library           ../libraries/DeviceLibrary.py    port=${PORT}


*** Variables ***
${PORT}           5025
${ROOT}           ${CURDIR}/../..


*** Keywords ***
Start Simulator
    [Documentation]    Start the simulator as a child process and wait until it accepts connections.
    ${python}=    Evaluate    sys.executable    modules=sys
    Start Process    ${python}    -m    device.simulator    --port    ${PORT}    --seed    1
    ...    cwd=${ROOT}    alias=simulator    stdout=${OUTPUT_DIR}/simulator.log    stderr=STDOUT
    Connect To Device    wait=10

Stop Simulator
    [Documentation]    Close the connection and stop the simulator process.
    Disconnect From Device
    Terminate All Processes

Reset Device
    [Documentation]    Factory reset, so every test starts from the same state.
    Command Should Return    RESET    OK
