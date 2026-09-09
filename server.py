#!/usr/bin/env python3
"""
server.py — Hardware MQTT client for the RampMe ramp.

Topics:
  ramp/{VEHICLE_ID}/cmd     (subscribe — this vehicle only, not a wildcard: a
                             unit must never react to another vehicle's command)
    { action: "new_reservation",    id: <int> }
    { action: "cancel_reservation", id: <int> }
    { action: "deploy" }

  ramp/{VEHICLE_ID}/state   (publish, retained)
    { state: "idle" | "deploying" | "deployed" | "retracting" | "done" | "error",
      reason?: str }

Wait time while deployed: PER_PASSENGER_SECONDS * len(active_reservation_ids)
(No base, as discussed.)
"""

import json
import os
import ssl
import threading
import time

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from dotenv import load_dotenv

load_dotenv()

from drivers.buzzer import Buzzer
from drivers.push_button import Button
from drivers.ramp import Ramp
from drivers.stepper_motor import StepperMotor
from utils.logger import log

GPIO.setmode(GPIO.BCM)

# ── Config ─────────────────────────────────────────────────────

VEHICLE_ID = os.environ.get("VEHICLE_ID", "2634")

# Reject MQTT wildcard/separator characters so CMD_TOPIC below always
# resolves to exactly this vehicle's topic, never a broader subscription.
_INVALID_VEHICLE_ID_CHARS = ("+", "#", "/")
if not VEHICLE_ID or any(c in VEHICLE_ID for c in _INVALID_VEHICLE_ID_CHARS):
    raise SystemExit(
        f"Invalid VEHICLE_ID {VEHICLE_ID!r}: must be non-empty and must not "
        f"contain any of {_INVALID_VEHICLE_ID_CHARS}"
    )

MQTT_URL = os.environ.get("MQTT_URL", "broker.hivemq.com")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "8883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
MQTT_USE_TLS = os.environ.get("MQTT_TLS", "true").lower() == "true"

PER_PASSENGER_SECONDS = 20
DOOR_POLL_INTERVAL = 0.5

CMD_TOPIC = f"ramp/{VEHICLE_ID}/cmd"

# ── Hardware init ──────────────────────────────────────────────

motor = StepperMotor()
buzzer = Buzzer()
deploy_button = Button(pin=16)
retract_button = Button(pin=12)
door = None

ramp = Ramp(
    motor=motor,
    deploy_button=deploy_button,
    retract_button=retract_button,
    buzzer=None,
    mock_door=door,
)

# ── Reservation state (local counter) ──────────────────────────

_lock = threading.Lock()
_active_ids: set[int] = set()
_sequence_running = False


def _active_count() -> int:
    with _lock:
        return len(_active_ids)


def _add_reservation(rid: int) -> None:
    with _lock:
        _active_ids.add(rid)
    log("INFO", "SERVER", f"Reservation added id={rid} (count={_active_count()})")


def _remove_reservation(rid: int) -> None:
    with _lock:
        _active_ids.discard(rid)
    log("INFO", "SERVER", f"Reservation cancelled id={rid} (count={_active_count()})")


def _clear_reservations() -> None:
    with _lock:
        _active_ids.clear()


# ── MQTT publisher ─────────────────────────────────────────────

_client: mqtt.Client | None = None


def publish_state(state: str, vehicle_id: str, reason: str | None = None) -> None:
    if _client is None:
        return
    payload: dict = {"state": state}
    if reason:
        payload["reason"] = reason
    topic = f"ramp/{vehicle_id}/state"
    _client.publish(topic, json.dumps(payload), qos=2, retain=True)
    log("INFO", "SERVER", f"→ [{vehicle_id}] state={state}" + (f" ({reason})" if reason else ""))


# ── Ramp sequence ──────────────────────────────────────────────


def _wait_for_door() -> None:
    if door is None:
        return
    log("INFO", "SERVER", "Waiting for door to open...")
    while True:
        if door.is_open() is True:
            log("INFO", "SERVER", "Door is open")
            return
        time.sleep(DOOR_POLL_INTERVAL)


def _wait_for_ramp() -> None:
    time.sleep(0.3)
    while ramp.is_moving:
        time.sleep(0.1)


def _ramp_sequence(vehicle_id: str) -> None:
    global _sequence_running

    try:
        wait_seconds = PER_PASSENGER_SECONDS * max(1, _active_count())

        _wait_for_door()

        publish_state("deploying", vehicle_id)
        ramp.deploy()
        _wait_for_ramp()
        publish_state("deployed", vehicle_id)

        log(
            "INFO",
            "SERVER",
            f"Waiting {wait_seconds}s for passengers (count={_active_count()})",
        )
        time.sleep(wait_seconds)

        publish_state("retracting", vehicle_id)
        ramp.retract()
        _wait_for_ramp()

        publish_state("done", vehicle_id)
        _clear_reservations()
        publish_state("idle", vehicle_id)

    except Exception as e:
        log("ERROR", "SERVER", f"Ramp sequence failed: {e}")
        publish_state("error", vehicle_id, reason=str(e))

    finally:
        with _lock:
            _sequence_running = False


def _trigger_deploy(vehicle_id: str) -> None:
    global _sequence_running
    with _lock:
        if _sequence_running:
            log("WARN", "SERVER", "Deploy requested but sequence already running")
            return
        if not _active_ids:
            log("WARN", "SERVER", "Deploy requested but no active reservations")
            return
        _sequence_running = True
    threading.Thread(target=_ramp_sequence, args=(vehicle_id,), daemon=True).start()


# ── MQTT callbacks ─────────────────────────────────────────────


def _on_connect(client, userdata, flags, rc, properties=None):
    if rc != 0:
        log("ERROR", "MQTT", f"Connection failed rc={rc}")
        return
    log("INFO", "MQTT", f"Connected to {MQTT_URL}:{MQTT_PORT}")
    client.subscribe(CMD_TOPIC, qos=2)
    log("INFO", "MQTT", f"Subscribed to {CMD_TOPIC}")


def _on_message(client, userdata, msg: mqtt.MQTTMessage):
    try:
        payload = json.loads(msg.payload)
    except Exception as e:
        log("ERROR", "MQTT", f"Bad payload on {msg.topic}: {e}")
        return

    action = payload.get("action")
    log("INFO", "MQTT", f"← [{VEHICLE_ID}] cmd action={action} payload={payload}")

    if action == "new_reservation":
        rid = payload.get("id")
        if isinstance(rid, int):
            _add_reservation(rid)

    elif action == "cancel_reservation":
        rid = payload.get("id")
        if isinstance(rid, int):
            _remove_reservation(rid)

    elif action == "deploy":
        _trigger_deploy(VEHICLE_ID)

    else:
        log("WARN", "MQTT", f"Unknown action: {action}")


# ── Main ───────────────────────────────────────────────────────


def main():
    global _client

    # Physical buttons still work for manual testing
    threading.Thread(target=ramp.run, daemon=True).start()

    client = mqtt.Client(
        client_id=f"rampme-hw-{VEHICLE_ID}",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    if MQTT_USE_TLS:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)

    # Will: broker publishes this if we disconnect ungracefully (uses VEHICLE_ID as fallback)
    client.will_set(
        f"ramp/{VEHICLE_ID}/state",
        json.dumps({"state": "error", "reason": "disconnected"}),
        qos=2,
        retain=True,
    )

    client.on_connect = _on_connect
    client.on_message = _on_message

    _client = client

    log(
        "INFO",
        "SERVER",
        f"Connecting to MQTT {MQTT_URL}:{MQTT_PORT} as vehicle {VEHICLE_ID}",
    )
    client.connect(MQTT_URL, MQTT_PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("INFO", "SERVER", "Shutting down")
    finally:
        if _client is not None:
            try:
                publish_state("idle", VEHICLE_ID, reason="shutdown")
                _client.disconnect()
            except Exception:
                pass
        ramp.stop()
        motor.disable()
        motor.cleanup()
        buzzer.cleanup()
        deploy_button.cleanup()
        retract_button.cleanup()
