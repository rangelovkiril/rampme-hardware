import time
from drivers.push_button import Button


def on_press():
    print("Button pressed!")


button = Button(pin=16, callback=on_press)

try:
    print("Testing is_pressed() polling for 5 seconds, hold the button down...")
    for _ in range(50):
        if button.is_pressed():
            print("Button is held down")
        time.sleep(0.1)

    print("\nNow testing callback mode for 10 seconds, press the button a few times...")
    time.sleep(10)

    print("\nDone.")

finally:
    button.cleanup()
