"""Robot Framework keyword library for talking to the sensor device.

Every public method here becomes a Robot keyword:
    connect_to_device        ->  Connect To Device
    send_command             ->  Send Command
    reading_should_be_within ->  Reading Should Be Within
"""

import re
import socket
import time

from robot.api import logger

READING = re.compile(r"(T|RH|CO2)=(\S+) (\S+)")


class DeviceLibrary:
    # One library instance for the whole test run, so the connection is shared.
    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, host="127.0.0.1", port=5025, timeout=2.0):
        self.host = host
        self.port = int(port)
        self.timeout = float(timeout)
        self._sock = None
        self._file = None

    # ---------- connection ----------

    def connect_to_device(self, wait=10.0):
        """Connect, retrying until the device is up or `wait` seconds pass."""
        deadline = time.monotonic() + float(wait)
        while True:
            try:
                self._sock = socket.create_connection((self.host, self.port), self.timeout)
                self._file = self._sock.makefile("rwb")
                logger.info(f"Connected to {self.host}:{self.port}")
                return
            except OSError:
                if time.monotonic() > deadline:
                    raise AssertionError(f"Device not reachable at {self.host}:{self.port}")
                time.sleep(0.2)

    def disconnect_from_device(self):
        if self._sock:
            self._file.close()
            self._sock.close()
            self._sock = self._file = None

    # ---------- commands ----------

    def send_command(self, command):
        """Send one command and return the device's answer line."""
        if not self._sock:
            raise AssertionError("Not connected. Use 'Connect To Device' first.")
        self._file.write((command + "\r\n").encode("ascii"))
        self._file.flush()
        answer = self._file.readline().decode("ascii").strip()
        logger.info(f">> {command}\n<< {answer}")
        return answer

    def command_should_return(self, command, expected):
        """Send a command and fail unless the answer is exactly `expected`."""
        answer = self.send_command(command)
        if answer != expected:
            raise AssertionError(f"'{command}' returned '{answer}', expected '{expected}'")

    # ---------- readings ----------

    def get_reading(self):
        """Send SEND and return a dict like {'T': 22.1, 'RH': 45.3, 'CO2': 605.0, 'unit': 'C'}.

        A broken sensor reports '***', which becomes None.
        """
        answer = self.send_command("SEND")
        found = READING.findall(answer)
        if len(found) != 3:
            raise AssertionError(f"Cannot parse reading: '{answer}'")
        reading = {}
        for name, value, unit in found:
            reading[name] = None if value == "***" else float(value)
            if name == "T":
                reading["unit"] = unit
        return reading

    def reading_should_be_within(self, quantity, low, high):
        """Take a fresh reading and check one quantity is between low and high."""
        value = self.get_reading()[quantity]
        if value is None:
            raise AssertionError(f"{quantity} sensor reports no value (***)")
        if not float(low) <= value <= float(high):
            raise AssertionError(f"{quantity}={value} is outside {low}..{high}")
        return value
