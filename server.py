#!/usr/bin/env python3
import threading
import time
import urllib.request
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from drivers.stepper_motor import StepperMotor
from drivers.buzzer import Buzzer
from drivers.push_button import Button
from drivers.mock_door import MockDoor
from drivers.ramp import Ramp
from utils.logger import log

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

BACKEND_URL = "https://rampme.site"
VEHICLE_ID = "2634"
PASSENGER_TIMEOUT = 30  # seconds to wait before retracting
DOOR_POLL_INTERVAL = 0.5  # seconds between door checks

# ── Hardware init ──────────────────────────────────────────────
motor = StepperMotor()
buzzer = Buzzer()
deploy_button = Button(pin=16)
retract_button = Button(pin=12)
door = MockDoor()

ramp = Ramp(
    motor=motor,
    deploy_button=deploy_button,
    retract_button=retract_button,
    buzzer=None,
    mock_door=door,
)

_lock = threading.Lock()
_running = False


def _notify_backend(ok: bool):
    try:
        body = json.dumps({"vehicle_id": VEHICLE_ID, "ok": ok}).encode()
        req = urllib.request.Request(
            f"{BACKEND_URL}/ramp/hardware/done",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
        log("INFO", "SERVER", "Backend notified")
    except Exception as e:
        log("ERROR", "SERVER", f"Backend notify failed: {e}")


def _wait_for_door():
    """Block until the door is open."""
    log("INFO", "SERVER", "Waiting for door to open...")
    while True:
        result = door.is_open()
        if result is True:
            log("INFO", "SERVER", "Door is open")
            return
        time.sleep(DOOR_POLL_INTERVAL)


def _wait_for_ramp():
    """Block until ramp finishes moving."""
    time.sleep(0.3)
    while ramp.is_moving:
        time.sleep(0.1)


def ramp_sequence():
    global _running
    ok = False

    try:
        # 1. Wait for the bus door to open
        _wait_for_door()

        # 2. Deploy
        log("INFO", "SERVER", "Deploying ramp")
        ramp.deploy()
        _wait_for_ramp()
        log("INFO", "SERVER", "Ramp deployed")

        # 3. Wait for passenger
        log("INFO", "SERVER", f"Waiting {PASSENGER_TIMEOUT}s for passenger")
        time.sleep(PASSENGER_TIMEOUT)

        # 4. Retract
        log("INFO", "SERVER", "Retracting ramp")
        ramp.retract()
        _wait_for_ramp()
        log("INFO", "SERVER", "Ramp retracted")

        ok = True

    except Exception as e:
        log("ERROR", "SERVER", f"Ramp sequence failed: {e}")

    finally:
        _notify_backend(ok)
        with _lock:
            _running = False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _running

        if self.path == "/status":
            with _lock:
                if not _running:
                    _running = True
                    threading.Thread(target=ramp_sequence, daemon=True).start()

            body = json.dumps(
                {
                    "at_stop": True,
                    "vehicle_id": VEHICLE_ID,
                    "ramp": ramp.get_status(),
                }
            ).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_):
        pass


def main():
    # Start button control loop in background (physical buttons still work)
    button_thread = threading.Thread(target=ramp.run, daemon=True)
    button_thread.start()

    log("INFO", "SERVER", "Hardware server starting on :5000")
    HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("INFO", "SERVER", "Shutting down")
    finally:
        ramp.stop()
        motor.disable()
        motor.cleanup()
        buzzer.cleanup()
        deploy_button.cleanup()
        retract_button.cleanup()
        door.close()
