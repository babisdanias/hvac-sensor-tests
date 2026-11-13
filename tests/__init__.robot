*** Settings ***
Documentation     Test suite for the HVS-100 mock HVAC sensor.
...               The simulator starts once for the whole run and stops at the end.
Resource          resources/common.resource
Suite Setup       Start Simulator
Suite Teardown    Stop Simulator
