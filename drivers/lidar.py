import time
from smbus2 import SMBus, i2c_msg
from utils.logger import log


class Lidar:
    def __init__(self, bus_id=1, address=0x10):
        self.bus_id = bus_id
        self.address = address
        self.distance = 0
        self.strength = 0
        self.temperature = 0

        # Header, Len, ID, Get Data, Checksum
        self.GET_DATA_CMD = [0x5A, 0x05, 0x00, 0x01, 0x60]
        self.KALMAN_FILTER_OFF_CMD = [0x5A, 0x05, 0x39, 0x00, 0x98]
        self.KALMAN_FILTER_ON_CMD = [0x5A, 0x05, 0x39, 0x01, 0x99]

        try:
            self.bus = SMBus(self.bus_id)
            log(
                "INFO",
                "LIDAR BUS" + str(self.bus_id),
                f"Initialized TFmini-S on I2C bus {bus_id} at {hex(address)}",
            )
        except Exception as e:
            log("ERROR", "LIDAR", f"Failed to open I2C bus: {e}")
            raise

    def _send_comand(self, command):
        try:
            write = i2c_msg.write(self.address, command)
            self.bus.i2c_rdwr(write)
            time.sleep(0.1)
            return True
        except Exception as e:
            log("ERROR", "LIDAR", f"Command {command} failed: {e}")
            return False

    def set_kalman_filter(self, active=True):
        cmd = self.KALMAN_FILTER_ON_CMD if active else self.KALMAN_FILTER_OFF_CMD
        status = "ON" if active else "OFF"

        if self._send_comand(cmd):
            log("INFO", "LIDAR", f"Kalman filter turned {status}")
            return True
        return False

    def update(self):
        """
        Triggers a measurement and updates the internal state.
        Returns True if successful, False otherwise.
        """
        try:
            write = i2c_msg.write(self.address, self.GET_DATA_CMD)

            read = i2c_msg.read(self.address, 9)

            self.bus.i2c_rdwr(write)

            time.sleep(0.01)

            self.bus.i2c_rdwr(read)
            data = list(read)

            if data[0] == 0x59 and data[1] == 0x59:
                checksum = sum(data[:8]) & 0xFF
                if checksum != data[8]:
                    log("WARN", "LIDAR", "Checksum mismatch")
                    return False

                self.distance = data[2] | (data[3] << 8)
                self.strength = data[4] | (data[5] << 8)

                temp_raw = data[6] | (data[7] << 8)
                self.temperature = (temp_raw / 8.0) - 256

                return True
            else:
                log("WARN", "LIDAR", f"Invalid frame header: {hex(data[0])}")
                return False

        except Exception as e:
            log("ERROR", "LIDAR", f"Read error: {e}")
            return False

    def get_data(self):
        """Returns the last valid reading."""
        return {
            "distance": self.distance,
            "strength": self.strength,
            "temperature": round(self.temperature, 2),
        }

    def close(self):
        self.bus.close()
        log("INFO", "LIDAR", "I2C bus closed")
