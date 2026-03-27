import time
import threading
from drivers.stepper_motor import StepperMotor
from drivers.buzzer import Buzzer
from drivers.push_button import Button
from drivers.mock_door import MockDoor
from utils.logger import log

DEPLOY_STEPS = 80000


class Ramp:
    def __init__(
        self,
        motor,
        deploy_button,
        retract_button,
        buzzer=None,
        mock_door=None,
        steps_per_tick=5,
        delay=0.0002,
    ):
        self.motor = motor
        self.deploy_button = deploy_button
        self.retract_button = retract_button
        self.buzzer = buzzer
        self.mock_door = mock_door
        self.steps_per_tick = steps_per_tick
        self.delay = delay

        self._buzzer_running = threading.Event()
        self._motor_moving = threading.Event()
        self._http_active = threading.Event()
        self._beep_thread = None
        self._running = False

        self.is_deployed = False
        self.is_moving = False

        log("INFO", "RAMP", "Ramp initialized")

    def get_status(self):
        return {
            "is_deployed": self.is_deployed,
            "is_moving": self.is_moving,
            "safe_to_move": not self.is_deployed and not self.is_moving,
        }

    def _door_is_clear(self):
        if self.mock_door is None:
            return True
        result = self.mock_door.is_open()
        if result is None:
            log("WARN", "RAMP", "Door sensor read failed — blocking movement")
            return False
        return result

    def _beep_loop(self):
        while self._buzzer_running.is_set():
            self.buzzer.beep(duration=0.39)
            time.sleep(0.2)

    def _start_buzzer(self):
        if self.buzzer and not self._buzzer_running.is_set():
            self._buzzer_running.set()
            self._beep_thread = threading.Thread(target=self._beep_loop, daemon=True)
            self._beep_thread.start()

    def _stop_buzzer(self):
        if self.buzzer and self._buzzer_running.is_set():
            self._buzzer_running.clear()
            if self._beep_thread:
                self._beep_thread.join(timeout=1.0)
                self._beep_thread = None

    def _stop_motor(self):
        if self._motor_moving.is_set():
            self.motor.disable()
            self._motor_moving.clear()
            self.is_moving = False
            self._stop_buzzer()
            log("INFO", "RAMP", "Motor stopped")

    def run(self):
        self._running = True
        log("INFO", "RAMP", "Ramp control loop started")

        try:
            while self._running:
                if self._http_active.is_set():
                    time.sleep(0.01)
                    continue

                if self.deploy_button.is_pressed():
                    if not self._motor_moving.is_set():
                        if not self._door_is_clear():
                            log(
                                "WARN", "RAMP", "Door is closed — button deploy blocked"
                            )
                            if self.buzzer:
                                self.buzzer.alert()
                            continue
                        self.motor.enable()
                        self.motor.set_direction(clockwise=True)
                        self._motor_moving.set()
                        self.is_moving = True
                        self.is_deployed = True
                        self._start_buzzer()
                        log("INFO", "RAMP", "Deploying ramp via button")
                    self.motor.step(steps=self.steps_per_tick, delay=self.delay)

                elif self.retract_button.is_pressed():
                    if not self._motor_moving.is_set():
                        self.motor.enable()
                        self.motor.set_direction(clockwise=False)
                        self._motor_moving.set()
                        self.is_moving = True
                        self.is_deployed = False
                        self._start_buzzer()
                        log("INFO", "RAMP", "Retracting ramp via button")
                    self.motor.step(steps=self.steps_per_tick, delay=self.delay)

                else:
                    self._stop_motor()

        except KeyboardInterrupt:
            pass
        finally:
            self._stop_motor()
            log("INFO", "RAMP", "Ramp control loop stopped")

    def stop(self):
        self._running = False

    def deploy(self):
        if self._motor_moving.is_set():
            log("WARN", "RAMP", "Deploy requested but motor already moving")
            return

        self._http_active.set()

        def _run():
            try:
                log("INFO", "RAMP", "Deploying ramp via request")

                if not self._door_is_clear():
                    log("WARN", "RAMP", "Door is closed — request deploy blocked")
                    if self.buzzer:
                        self.buzzer.alert()
                    return

                self.motor.enable()
                self.motor.set_direction(clockwise=True)
                self._motor_moving.set()
                self.is_moving = True
                self.is_deployed = True
                self._start_buzzer()

                steps_done = 0
                while steps_done < DEPLOY_STEPS:
                    self.motor.step(steps=self.steps_per_tick, delay=self.delay)
                    steps_done += self.steps_per_tick

                self._stop_motor()
                log("INFO", "RAMP", "Deploy complete")
            finally:
                self._http_active.clear()

        threading.Thread(target=_run, daemon=True).start()

    def retract(self):
        if self._motor_moving.is_set():
            log("WARN", "RAMP", "Retract requested but motor already moving")
            return

        self._http_active.set()

        def _run():
            try:
                log("INFO", "RAMP", "Retracting ramp via request")
                self.motor.enable()
                self.motor.set_direction(clockwise=False)
                self._motor_moving.set()
                self.is_moving = True
                self.is_deployed = False
                self._start_buzzer()

                steps_done = 0
                while steps_done < DEPLOY_STEPS:
                    self.motor.step(steps=self.steps_per_tick, delay=self.delay)
                    steps_done += self.steps_per_tick

                self._stop_motor()
                log("INFO", "RAMP", "Retract complete")
            finally:
                self._http_active.clear()

        threading.Thread(target=_run, daemon=True).start()
