import time
import threading
from drivers.stepper_motor import StepperMotor
from drivers.buzzer import Buzzer
from drivers.push_button import Button
from utils.logger import log


class Ramp:
    def __init__(
        self,
        motor,
        deploy_button,
        retract_button,
        buzzer=None,
        steps_per_tick=5,
        delay=0.00007,
    ):
        """
        Controls the ramp using two buttons and a stepper motor.

        Args:
            motor (StepperMotor): The stepper motor instance.
            deploy_button (Button): Button that deploys (extends) the ramp.
            retract_button (Button): Button that retracts the ramp.
            buzzer (Buzzer): Optional buzzer instance. Pass None to disable.
            steps_per_tick (int): Steps to move per polling loop iteration.
            delay (float): Delay between steps (controls speed).
        """
        self.motor = motor
        self.deploy_button = deploy_button
        self.retract_button = retract_button
        self.buzzer = buzzer
        self.steps_per_tick = steps_per_tick
        self.delay = delay

        self._buzzer_running = threading.Event()
        self._motor_moving = threading.Event()
        self._beep_thread = None
        self._running = False

        log("INFO", "RAMP", "Ramp initialized")

    def _beep_loop(self):
        while self._buzzer_running.is_set():
            self.buzzer.beep(duration=0.39)
            time.sleep(0.2)

    def _start_buzzer(self):
        if self.buzzer and not self._buzzer_running.is_set():
            self._buzzer_running.set()
            self._beep_thread = threading.Thread(
                target=self._beep_loop, daemon=True
            )
            self._beep_thread.start()

    def _stop_buzzer(self):
        if self.buzzer and self._buzzer_running.is_set():
            self._buzzer_running.clear()
            if self._beep_thread:
                self._beep_thread.join()
                self._beep_thread = None

    def _stop_motor(self):
        if self._motor_moving.is_set():
            self.motor.disable()
            self._motor_moving.clear()
            self._stop_buzzer()
            log("INFO", "RAMP", "Motor stopped")

    def run(self):
        """
        Starts the main polling loop. Blocks until Ctrl+C or stop() is called.
        """
        self._running = True
        log("INFO", "RAMP", "Ramp control loop started")

        try:
            while self._running:
                if self.deploy_button.is_pressed():
                    if not self._motor_moving.is_set():
                        self.motor.enable()
                        self.motor.set_direction(clockwise=True)
                        self._motor_moving.set()
                        self._start_buzzer()
                        log("INFO", "RAMP", "Deploying ramp")
                    self.motor.step(steps=self.steps_per_tick, delay=self.delay)

                elif self.retract_button.is_pressed():
                    if not self._motor_moving.is_set():
                        self.motor.enable()
                        self.motor.set_direction(clockwise=False)
                        self._motor_moving.set()
                        self._start_buzzer()
                        log("INFO", "RAMP", "Retracting ramp")
                    self.motor.step(steps=self.steps_per_tick, delay=self.delay)

                else:
                    self._stop_motor()

                time.sleep(0.001)

        except KeyboardInterrupt:
            pass
        finally:
            self._stop_motor()
            log("INFO", "RAMP", "Ramp control loop stopped")

    def stop(self):
        """
        Stops the main polling loop.
        """
        self._running = False