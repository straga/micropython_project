from micropython import const
import ustruct
import sys


_HUMID_NOHOLD = const(0xf5)
_TEMP_NOHOLD = const(0xf3)
_RESET = const(0xfe)
_READ_USER1 = const(0xe7)
_USER1_VAL = const(0x3a)


def _crc(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for i in range(8):
            if crc & 0x80:
                crc <<= 1
                crc ^= 0x131
            else:
                crc <<= 1
    return crc


class SI7021:
    """
    A driver for the SI7021 temperature and humidity sensor.

    MicroPython example::

        import si7021
        from machine import I2C, Pin

        i2c = I2C(-1, Pin(5), Pin(4))
        s = si7021.SI7021(i2c)
        print(s.temperature())
        print(s.humidity())

    """

    def __init__(self, i2c, address=0x40):
        self.i2c = i2c
        self.address = address
        self.init()
        self._measurement = 0

    def init(self):
        self.reset()
        # Make sure the USER1 settings are correct.
        while True:
            # While restarting, the sensor doesn't respond to reads or writes.
            try:
                value = self.i2c.readfrom_mem(self.address, _READ_USER1, 1)[0]
            except OSError as e:
                if e.args[0] != 19: # errno 19 ENODEV
                    raise
            else:
                break
        if value != _USER1_VAL:
            raise RuntimeError("bad USER1 register (%x!=%x)" % (
                value, _USER1_VAL))

    def _command(self, command):
        self.i2c.writeto(self.address, ustruct.pack('B', command))

    def _data(self):
        data = bytearray(3)
        data[0] = 0xff
        while True:
            # While busy, the sensor doesn't respond to reads.
            try:
                self.i2c.readfrom_into(self.address, data)
            except OSError as e:
                if e.args[0] != 19: # errno 19 ENODEV
                    raise
            else:
                if data[0] != 0xff: # Check if read succeeded.
                    break
        value, checksum = ustruct.unpack('>HB', data)
        if checksum != _crc(data[:2]):
            raise ValueError("CRC mismatch")
        return value

    def reset(self):
        self._command(_RESET)

    def humidity(self, raw=False, block=True):
        """
        Start a humidity measurement.

        If ``block`` is ``True``, block until it is ready and return the
        measured value. If it's ``False``, return None immediately, and the
        value can be read later with a blocking call.

        If ``raw`` is ``True``, return the measured value as 16-bit integer,
        otherwise convert it into percentage of relative humidity and return it
        as a floating point number.
        """

        if not self._measurement:
            self._command(_HUMID_NOHOLD)
        elif self._measurement != _HUMID_NOHOLD:
            raise RuntimeError("other measurement in progress")
        if not block:
            self._measurement = _HUMID_NOHOLD
            return None
        self._measurement = 0
        value = self._data()
        if raw:
            return value
        return value * 125 / 65536 - 6

    def temperature(self, raw=False, block=True):
        """
        Start a temperature measurement.

        If ``block`` is ``True``, block until it is ready and return the
        measured value. If it's ``False``, return None immediately, and the
        value can be read later with a blocking call.

        If ``raw`` is ``True``, return the measured value as 16-bit integer,
        otherwise convert it into Celsius degrees and return as a floating
        point number.
        """
        if not self._measurement:
            self._command(_TEMP_NOHOLD)
        elif self._measurement != _TEMP_NOHOLD:
            raise RuntimeError("other measurement in progress")
        if not block:
            self._measurement = _TEMP_NOHOLD
            return None
        self._measurement = 0
        value = self._data()
        if raw:
            return value
        return value * 175.72 / 65536 - 46.85
