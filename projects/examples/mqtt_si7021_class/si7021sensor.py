class SI7021sensor():
    __slots__ = 'publish_state_to_mqtt', 'sensor_type'
    sensor_type = "si7021"

    def __init__(self):
        import si7021
        from machine import I2C, Pin
        try:
            i2c = I2C(sda=Pin(5), scl=Pin(4))
            self.sensor = si7021.SI7021(i2c)
        except:
            print("Debug: Unable to initialize sensor")

    def measure(self):
        try:
            if (self.sensor.temperature() and self.sensor.humidity()):
                temperature, humidity = (
                    self.sensor.temperature(), self.sensor.humidity())
                return temperature, humidity
        except:
            print("Debug: Unable to read the data from sensor")
