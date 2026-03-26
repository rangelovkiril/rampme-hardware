import time
from drivers.buzzer import Buzzer

buzzer = Buzzer()

try:
    print("Single beep...")
    buzzer.beep()
    time.sleep(1)

    print("3 beeps...")
    buzzer.beep_n(n=3)
    time.sleep(1)

    print("5 beeps fast...")
    buzzer.beep_n(n=5, duration=0.1, gap=0.1)
    time.sleep(1)

    print("Alert pattern...")
    buzzer.alert()
    time.sleep(1)

    print("Long beep (1 second)...")
    buzzer.beep(duration=1)
    time.sleep(1)

    print("Buzzer on for 2 seconds then off...")
    buzzer.on()
    time.sleep(2)
    buzzer.off()
    time.sleep(1)

    print("Done.")

finally:
    buzzer.cleanup()
