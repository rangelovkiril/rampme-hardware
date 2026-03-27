from drivers.lidar import Lidar
from utils.logger import log


class MockDoor:
    def __init__(self, closed_threshold_cm=20, bus_id=1, address=0x10):
        """
        Uses LiDAR distance to simulate whether a bus door is open or closed.

        Args:
            closed_threshold_cm (int): Distance in cm below which the door
                                       is considered closed. Default 20cm.
            bus_id (int): I2C bus ID for the LiDAR.
            address (int): I2C address of the LiDAR.
        """
        self.closed_threshold_cm = closed_threshold_cm
        self.lidar = Lidar(bus_id=bus_id, address=address)
        log("INFO", "MOCK_DOOR", f"MockDoor initialized — closed threshold: {closed_threshold_cm}cm")

    def is_open(self):
        """
        Returns True if the door appears open, False if closed.
        Returns None if the LiDAR read failed.
        """
        if not self.lidar.update():
            log("WARN", "MOCK_DOOR", "LiDAR read failed — door state unknown")
            return None

        data = self.lidar.get_data()
        distance = data["distance"]
        open = distance > self.closed_threshold_cm

        log(
            "INFO",
            "MOCK_DOOR",
            f"Distance: {distance}cm — door is {'OPEN' if open else 'CLOSED'}"
        )
        return open

    def close(self):
        self.lidar.close()
        