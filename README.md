# HVS-100 sensor test automation

![Robot tests](https://github.com/babisdanias/hvac-sensor-tests/actions/workflows/tests.yml/badge.svg)

Test automation for a mock HVAC sensor, built with **Robot Framework** and **Python**, and run automatically on every push with **GitHub Actions** (a **Jenkinsfile** for the same pipeline is included).

The device under test is a small simulator that measures temperature, relative humidity and CO2. It speaks a line-based text protocol, as many real measurement devices do over a serial port. Here it runs over TCP, so the whole setup works on any machine and in CI, without hardware.

## What is tested

26 test cases in 5 suites:

| Suite | What it checks |
|---|---|
| `01_identity` | Model, firmware, serial number format, health status |
| `02_measurements` | Readings in normal range, stable over time, follow the environment (data-driven) |
| `03_units` | Celsius/Fahrenheit switching and conversion, invalid units, reset |
| `04_errors` | Unknown commands, syntax errors, case handling, recovery after bad input |
| `05_faults_and_alarms` | Sensor faults, out-of-range saturation, CO2 alarm threshold (incl. boundary value), invalid thresholds |

Tests tagged `smoke` give a quick health check. CI runs the smoke set first, then the full regression suite.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
robot --outputdir results tests          # all tests
robot --include smoke --outputdir results tests   # smoke only
```

Open `results/report.html` in a browser to see the results, and `results/log.html` for every command sent and every answer received.

To talk to the device by hand:

```bash
python -m device.simulator --port 5025
# in another terminal:
nc localhost 5025
SEND
T=22.1 C RH=45.3 %RH CO2=605 ppm
```

## Device protocol

One command per line. The device answers with one line.

| Command | Answer |
|---|---|
| `HELP` | List of commands |
| `VERS` | `HVS-100 1.2.0` |
| `SNUM` | Serial number, e.g. `A1234567` |
| `SEND` | `T=22.1 C RH=45.3 %RH CO2=605 ppm` (a failed sensor shows `***`) |
| `STATUS` | `OK`, or problems joined with `;` (e.g. `ERR RH SENSOR`, `ERR T OUT OF RANGE`, `ALARM CO2`) |
| `UNIT` / `UNIT C` / `UNIT F` | Show or set the temperature unit |
| `ALARM` / `ALARM CO2 <ppm>` | Show or set the CO2 alarm threshold |
| `RESET` | Back to factory settings |
| `TEST ENV <T\|RH\|CO2> <value>` | Test hook: set the simulated environment |
| `TEST FAULT <T\|RH\|CO2>` / `TEST CLEAR` | Test hook: break a sensor / clear faults |
| `QUIT` | Close the connection |

Errors: `ERR 01 UNKNOWN COMMAND`, `ERR 02 SYNTAX`, `ERR 03 INVALID VALUE`.

## Layout

```
device/simulator.py           the device under test
tests/__init__.robot          starts the simulator once for the whole run
tests/resources/common.resource   shared keywords (start, stop, reset)
tests/libraries/DeviceLibrary.py  Python keyword library: connect, send, parse readings
tests/0*_*.robot              the test suites
.github/workflows/tests.yml   GitHub Actions pipeline
Jenkinsfile                   same pipeline for Jenkins
```