import RPi.GPIO as GPIO
import time
from utils.logger import log


class Buzzer:
    def __init__(self, pin=17):
        """
        Initializes the buzzer GPIO pin.

        Args:
            pin (int): BCM pin connected to the transistor base via 1kΩ resistor.
        """
        self.pin = pin

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

        log("INFO", "BUZZER", "Buzzer initialized")

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)

    def beep(self, duration=0.2):
        """
        Produces a single beep.

        Args:
            duration (float): How long the beep lasts in seconds.
        """
        self.on()
        time.sleep(duration)
        self.off()

    def beep_n(self, n=3, duration=0.2, gap=0.2):
        """
        Produces n beeps with a gap between them.

        Args:
            n (int): Number of beeps.
            duration (float): How long each beep lasts in seconds.
            gap (float): Silence between beeps in seconds.
        """
        for i in range(n):
            self.beep(duration)
            if i < n - 1:
                time.sleep(gap)

        log("INFO", "BUZZER", f"Beeped {n} times")

    def alert(self):
        """
        Produces a rapid alert pattern — 5 short beeps.
        """
        self.beep_n(n=5, duration=0.1, gap=0.1)
        log("INFO", "BUZZER", "Alert pattern triggered")

    def cleanup(self):
        """
        Turns off buzzer and releases GPIO pin.
        Should be called during system shutdown.
        """
        self.off()
        GPIO.cleanup([self.pin])
        log("INFO", "BUZZER", "Pins cleaned up")