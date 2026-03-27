import RPi.GPIO as GPIO
from utils.logger import log


class Button:
    def __init__(self, pin=16, callback=None):
        """
        Initializes the button GPIO pin with internal pull-down resistor.

        Args:
            pin (int): BCM pin connected to the NO terminal of the button.
            callback (callable): Optional function to call when button is pressed.
        """
        self.pin = pin
        self.callback = callback

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        if callback:
            GPIO.add_event_detect(
                self.pin, GPIO.RISING, callback=self._on_press, bouncetime=200
            )

        log("INFO", "BUTTON", f"Button initialized on pin {self.pin}")

    def _on_press(self, channel):
        log("INFO", "BUTTON", f"Button pressed on pin {self.pin}")
        if self.callback:
            self.callback()

    def is_pressed(self):
        return GPIO.input(self.pin) == GPIO.HIGH

    def set_callback(self, callback):
        self.callback = callback
        GPIO.add_event_detect(
            self.pin, GPIO.RISING, callback=self._on_press, bouncetime=200
        )

    def cleanup(self):
        GPIO.cleanup([self.pin])
        log("INFO", "BUTTON", f"Pin {self.pin} cleaned up")