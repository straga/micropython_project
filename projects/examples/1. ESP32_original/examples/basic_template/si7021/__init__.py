
from ustruct import unpack as unp
from ustruct import pack as pk
import math

import logging
import uasyncio as asyncio

log = logging.getLogger("SI7021")
log.setLevel(logging.INFO)

from micropython import const


__SI_ADDR = const(0x40)
__SI_RH_READ = const(0xE5)
__SI_TEMP_READ = const(0xE3)
__SI_POST_RH_TEMP_READ = const(0xE0)
__SI_RESET = const(0xFE)
__SI_USER1_READ = const(0xE7)
__SI_USER1_WRITE = const(0xE6)
__SI_CRC8_POLYNOMINAL = const(0x13100)  # CRC8 polynomial for 16bit CRC8 x^8 + x^5 + x^4 + 1
__SI_TRIGGER_TEMP_MEASURE_HOLD = const(0xE3)
__SI_TRIGGER_HUMD_MEASURE_HOLD = const(0xE5)
__SI_TRIGGER_TEMPERATURE_NO_HOLD = const(0xF3)
__SI_TRIGGER_HUMIDITY_NO_HOLD = const(0xF5)


class SI7021:

    def __init__(self, i2c):

        self.i2c = i2c

        self.si_exists = False
        self.status = 0

        self._raw = {}

        self.delays = 100 #ms
        self.read_delay = 10 #s

        self.run = False

        self.temperature = False
        self.humidity = False

        self.cb = None


        log.debug("Init done!")



    def sensor_detect(self):

        try:
            reg = self.i2c.readfrom_mem(__SI_ADDR, __SI_USER1_READ, 1)
        except Exception as e:
            self.status = 0
            log.debug("Sensor Error or not present: {}")
            self.soft_reset()
            return self.status

        log.debug("Sensor present / Register Byte: {}, decimal: {}".format(reg[0], reg))

        self.status = 1
        return self.status



    def soft_reset(self):
        try:
            self.i2c.writeto(__SI_ADDR, pk('b', __SI_RESET))
        except Exception as e:
            log.debug("Sensor Error or not present: {}".format(e))
            return None
        return True



    async def _read_data(self, raw=None):

        c_try = 0
        while True:
            data = None
            try:
                data = self.i2c.readfrom(__SI_ADDR, 3)
            except Exception:
                pass

            if data:
                self._raw[raw] = data
                break

            if c_try > 3:
                self.status = 0
                log.debug("Sensor Get Data Error")
                break

            c_try += 1
            await asyncio.sleep_ms(5)  # Wait for device



    async def _get_data(self):

        # TEMPERATURE_NO_HOLD
        try:
            self.i2c.writeto(__SI_ADDR, pk('b', __SI_TRIGGER_TEMPERATURE_NO_HOLD))
        except Exception as e:
            log.debug("Sensor Temp cmd: {}".format(e))
            self.status = 0

        await asyncio.sleep_ms(self.delays)  # Wait for device
        await self._read_data("T")


        # HUMIDITY_NO_HOLD
        try:
            self.i2c.writeto(__SI_ADDR, pk('b', __SI_TRIGGER_HUMIDITY_NO_HOLD))
        except Exception as e:
            log.debug("Sensor Humidity cmd Error: {}".format(e))
            self.status = 0

        await asyncio.sleep_ms(self.delays)  # Wait for device
        await self._read_data("H")

        return True


    def _temperature(self):
        '''
        Temperature in degree C.
        '''

        try:
            raw_t = self._raw["T"]
        except Exception as e:
            log.debug("Temperature convert Error: {}".format(e))
            return False

        if not self.crc8check(raw_t):
            log.debug("crc8check raw T: {} - False, ".format(raw_t))
            return False


        raw_temp = (raw_t[0] << 8) + raw_t[1]

        # Clear the status bits
        raw_temp = raw_temp & 0xFFFC

        # Calculate the actual temperature
        actual_temp = -46.85 + (175.72 * raw_temp / 65536)

        log.debug("Temperature: {} .C".format(actual_temp))
        return actual_temp





    def _humidity(self):
        '''
        Humidity in RH.
        '''

        try:
            raw_h = self._raw["H"]
        except Exception as e:
            log.debug("Humidity convert error: {}".format(e))
            return None

        if not self.crc8check(raw_h):
            log.debug("crc8check raw T: {} - False, ".format(raw_h))
            return None

        raw_rh = (raw_h[0] << 8) + raw_h[1]

        # Clear the status bits
        raw_rh = raw_rh & 0xFFFC

        # Calculate the actual RH
        actual_rh = -6 + (125.0 * raw_rh / 65536)

        log.debug("Humidity: {} RH".format(actual_rh))

        return actual_rh



    def crc8check(self, value):
        if not value:
            return False

        remainder = ((value[0] << 8) + value[1]) << 8
        remainder |= value[2]

        # POLYNOMIAL = 0x0131 = x^8 + x^5 + x^4 + 1
        # divsor = 0x988000 is polynomial shifted to farthest left of three bytes
        divsor = 0x988000

        for i in range(0, 16):
            if (remainder & 1 << (23 - i)):
                remainder ^= divsor
            divsor = divsor >> 1

        if remainder == 0:
            return True
        else:
            return False

    def set_callback(self, f):
        self.cb = f


    def dataldump(self):
        return [self.temperature, self.humidity]


    async def _run(self):
        log.info("Coro Run")
        while True:

            if self.status == 0:
                self.temperature = False
                self.humidity = False

                self.sensor_detect()

                await asyncio.sleep(5)
            else:

                raw_data = await self._get_data()

                if raw_data:
                    self.temperature = self._temperature()
                    self.humidity = self._humidity()

                if self.cb:
                    self.cb()

                await asyncio.sleep(self.read_delay)


    def start(self):

        loop = asyncio.get_event_loop()

        if not self.run:
            loop.create_task(self._run())
            log.info("Coro started")
            self.run = True

        return True
