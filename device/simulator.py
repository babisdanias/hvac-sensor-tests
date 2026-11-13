"""Mock HVAC sensor device.

A small TCP server that behaves like a measurement device for temperature,
relative humidity and CO2. You talk to it with one text command per line,
and it answers with one line. Real devices often speak a protocol like this
over a serial port; here we use TCP so it runs anywhere, including CI.

Run it:
    python -m device.simulator --port 5025

Try it by hand (in another terminal):
    nc localhost 5025
    SEND
"""

import argparse
import random
import socketserver
import threading

MODEL = "HVS-100"
FIRMWARE = "1.2.0"

# What the sensor can physically measure. Outside this range it saturates.
RANGES = {"T": (-40.0, 60.0), "RH": (0.0, 100.0), "CO2": (0.0, 5000.0)}

# How much random noise each reading gets, to behave like a real sensor.
NOISE = {"T": 0.2, "RH": 0.5, "CO2": 5.0}

ERR_UNKNOWN = "ERR 01 UNKNOWN COMMAND"
ERR_SYNTAX = "ERR 02 SYNTAX"
ERR_VALUE = "ERR 03 INVALID VALUE"


class Device:
    """The device's state and command logic. Knows nothing about networking."""

    def __init__(self, serial="A1234567", seed=None):
        self.serial = serial
        self.rng = random.Random(seed)
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.unit = "C"
        self.co2_alarm = 1000.0
        # The "room" the sensor sits in. Tests can change it with TEST ENV.
        self.env = {"T": 22.0, "RH": 45.0, "CO2": 600.0}
        self.faults = set()

    # ---------- measurement ----------

    def _read(self, quantity):
        """One raw reading, with noise, clipped to the sensor's range."""
        low, high = RANGES[quantity]
        value = self.env[quantity] + self.rng.uniform(-NOISE[quantity], NOISE[quantity])
        return min(max(value, low), high)

    def _out_of_range(self):
        return [q for q, (low, high) in RANGES.items() if not low <= self.env[q] <= high]

    def send(self):
        t = self._read("T")
        if self.unit == "F":
            t = t * 9 / 5 + 32
        parts = [
            "***" if "T" in self.faults else f"{t:.1f}",
            "***" if "RH" in self.faults else f"{self._read('RH'):.1f}",
            "***" if "CO2" in self.faults else f"{self._read('CO2'):.0f}",
        ]
        return f"T={parts[0]} {self.unit} RH={parts[1]} %RH CO2={parts[2]} ppm"

    def status(self):
        problems = [f"ERR {q} SENSOR" for q in sorted(self.faults)]
        problems += [f"ERR {q} OUT OF RANGE" for q in self._out_of_range()]
        if "CO2" not in self.faults and self.env["CO2"] > self.co2_alarm:
            problems.append("ALARM CO2")
        return ";".join(problems) if problems else "OK"

    # ---------- command handling ----------

    def handle(self, line):
        """Take one command line, return one response line."""
        words = line.strip().upper().split()
        if not words:
            return ERR_SYNTAX
        cmd, args = words[0], words[1:]
        with self.lock:
            handler = getattr(self, f"_cmd_{cmd}", None)
            if handler is None:
                return ERR_UNKNOWN
            return handler(args)

    def _cmd_HELP(self, args):
        return "COMMANDS: HELP VERS SNUM SEND STATUS UNIT ALARM RESET QUIT"

    def _cmd_VERS(self, args):
        return f"{MODEL} {FIRMWARE}"

    def _cmd_SNUM(self, args):
        return self.serial

    def _cmd_SEND(self, args):
        return self.send() if not args else ERR_SYNTAX

    def _cmd_STATUS(self, args):
        return self.status()

    def _cmd_RESET(self, args):
        self.reset()
        return "OK"

    def _cmd_UNIT(self, args):
        if not args:
            return self.unit
        if len(args) != 1 or args[0] not in ("C", "F"):
            return ERR_VALUE
        self.unit = args[0]
        return "OK"

    def _cmd_ALARM(self, args):
        # ALARM            -> show threshold
        # ALARM CO2 1200   -> set threshold
        if not args:
            return f"CO2 {self.co2_alarm:.0f}"
        if len(args) != 2 or args[0] != "CO2":
            return ERR_SYNTAX
        try:
            value = float(args[1])
        except ValueError:
            return ERR_VALUE
        if not RANGES["CO2"][0] < value <= RANGES["CO2"][1]:
            return ERR_VALUE
        self.co2_alarm = value
        return "OK"

    def _cmd_TEST(self, args):
        """Test hooks, like a service port on a real device.

        TEST ENV T 30      -> set the room temperature to 30 C
        TEST FAULT RH      -> break the humidity sensor
        TEST CLEAR         -> remove all faults
        """
        if args[:1] == ["ENV"] and len(args) == 3 and args[1] in RANGES:
            try:
                self.env[args[1]] = float(args[2])
            except ValueError:
                return ERR_VALUE
            return "OK"
        if args[:1] == ["FAULT"] and len(args) == 2 and args[1] in RANGES:
            self.faults.add(args[1])
            return "OK"
        if args == ["CLEAR"]:
            self.faults.clear()
            return "OK"
        return ERR_SYNTAX


class Handler(socketserver.StreamRequestHandler):
    """Reads lines from one client and writes answers back."""

    def handle(self):
        for raw in self.rfile:
            line = raw.decode("ascii", errors="replace").strip()
            if line.upper() == "QUIT":
                self.wfile.write(b"BYE\r\n")
                return
            answer = self.server.device.handle(line)
            self.wfile.write((answer + "\r\n").encode("ascii"))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="Mock HVAC sensor device")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5025)
    parser.add_argument("--seed", type=int, default=None, help="fixed noise, for repeatable runs")
    opts = parser.parse_args()

    with Server((opts.host, opts.port), Handler) as server:
        server.device = Device(seed=opts.seed)
        print(f"{MODEL} simulator listening on {opts.host}:{opts.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
