import time
from drivers.lidar import Lidar

lidar = Lidar()

try:
    print("=== Test 1: Single reading ===")
    if lidar.update():
        data = lidar.get_data()
        print(f"Distance:    {data['distance']} cm")
        print(f"Strength:    {data['strength']}")
        print(f"Temperature: {data['temperature']} °C")
    else:
        print("Failed to get reading")

    time.sleep(1)

    print("\n=== Test 2: Kalman filter off then on ===")
    lidar.set_kalman_filter(active=False)
    time.sleep(0.5)
    lidar.set_kalman_filter(active=True)
    time.sleep(0.5)

    print("\n=== Test 3: Continuous readings for 10 seconds ===")
    start = time.time()
    while time.time() - start < 10:
        if lidar.update():
            data = lidar.get_data()
            print(
                f"Distance: {data['distance']:4d} cm | Strength: {data['strength']:5d} | Temp: {data['temperature']} °C"
            )
        else:
            print("Read failed")
        time.sleep(0.1)

    print("\nDone.")

finally:
    lidar.close()
