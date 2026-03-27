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

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        if callback:
            GPIO.add_event_detect(
                self.pin, GPIO.RISING, callback=self._on_press, bouncetime=200
            )

        log("INFO", "BUTTON", f"Button initialized on pin {self.pin}")

    def _on_press(self, channel):
        """
        Internal interrupt handler — calls user callback on press.
        """
        log("INFO", "BUTTON", f"Button pressed on pin {self.pin}")
        if self.callback:
            self.callback()

    def is_pressed(self):
        """
        Returns True if the button is currently held down.

        Returns:
            bool: True if pressed, False otherwise.
        """
        return GPIO.input(self.pin) == GPIO.HIGH

    def set_callback(self, callback):
        """
        Sets or replaces the callback for button press events.

        Args:
            callback (callable): Function to call when button is pressed.
        """
        self.callback = callback
        GPIO.add_event_detect(
            self.pin, GPIO.RISING, callback=self._on_press, bouncetime=200
        )

    def cleanup(self):
        """
        Releases GPIO pin. Should be called during system shutdown.
        """
        GPIO.cleanup([self.pin])
        log("INFO", "BUTTON", f"Pin {self.pin} cleaned up")
