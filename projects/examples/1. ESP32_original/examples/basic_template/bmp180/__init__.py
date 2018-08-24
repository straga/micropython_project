

from ustruct import unpack as unp
from ustruct import pack as pk
import math


import logging
import uasyncio as asyncio


log = logging.getLogger("BMP180")
log.setLevel(logging.INFO)


from micropython import const

_BMP_ADDR = const(119)
_BMP_CONTROL = const(0xF4)
_BMP_READ_TEMP_CMD = const(0x2E)
_BMP_READ_PRESURE_CMD = const(0x34)


class BMP180():

    def __init__(self, i2c):

        self.i2c = i2c
        self.chip_id = None
        self.status = 0

        # calibration data from EEPROM
        self._clb = {}


        # adjusted by user
        self.oversample_setting = 3
        self.baseline = 101325.0

        # output raw
        self._raw = {}

        self.delays = (5, 8, 14, 25) #ms
        self.read_delay = 10 #s

        self.run = False

        self.temperature = False
        self.pressure = False
        self.altitude = False

        self.cb = None

        log.debug("Init done!")

    def sensor_detect(self):

        try:
            self.chip_id = self.i2c.readfrom_mem(_BMP_ADDR, 0xD0, 1)  # chip id adress 0xD0 = always /x55
        except Exception as e:
            self.status = 0
            log.debug("Sensor Error or not present: {}".format(e))
            return self.status

        self.status = 1

        reg_cal_h = {"AC1": 0xAA, "AC2": 0xAC, "AC3": 0xAE, "B1": 0xB6, "B2": 0xB8, "MB": 0xBA, "MC": 0xBC, "MD": 0xBE}
        reg_cal_H = {"AC4": 0xB0, "AC5": 0xB2, "AC6": 0xB4}

        # read calibration data from EEPROM

        if not self._clb:
            for key, val in reg_cal_h.items():
                self._clb[key] = unp('>h', self.i2c.readfrom_mem(_BMP_ADDR, val,2))[0]

            for key, val in reg_cal_H.items():
                self._clb[key] = unp('>H', self.i2c.readfrom_mem(_BMP_ADDR, val, 2))[0]

            log.debug("Sensor calibration data: {}".format(self._clb))

        log.debug("Sensor present: {}".format(self.status))

        return self.status


    async def _get_data(self):

            # Read Temperature
            try:
                self.i2c.writeto_mem(_BMP_ADDR, _BMP_CONTROL, pk('I', _BMP_READ_TEMP_CMD))
            except Exception as e:
                log.debug("Sensor Temp cmd: {}".format(e))
                self.status = 0

            await asyncio.sleep_ms(self.delays[0])  # Wait for device

            try:
                self._raw["UT"] = self.i2c.readfrom_mem(_BMP_ADDR, 0xF6, 2)
            except Exception as e:
                log.debug("Sensor Temp data: {}".format(e))
                self.status = 0

            # Read PRESSURE after Temperature

            com_pressure = _BMP_READ_PRESURE_CMD + (self.oversample_setting << 6)

            try:
                self.i2c.writeto_mem(_BMP_ADDR, _BMP_CONTROL, pk('I', com_pressure))
            except Exception as e:
                log.debug("Sensor Pressure cmd: {}".format(e))
                self.status = 0

            await asyncio.sleep_ms(self.delays[self.oversample_setting])  # Wait for device oversample_setting

            try:
                self._raw["MSB"] = self.i2c.readfrom_mem(_BMP_ADDR, 0xF6, 1)
                self._raw["LSB"] = self.i2c.readfrom_mem(_BMP_ADDR, 0xF7, 1)
                self._raw["XLSB"] = self.i2c.readfrom_mem(_BMP_ADDR, 0xF8, 1)
            except Exception as e:
                log.debug("Sensor Pressure data: {}".format(e))
                self.status = 0

            return True



    def _temperature(self):
        '''
        Temperature in degree C.
        '''

        try:
            UT = unp('>H', self._raw["UT"])[0]
        except Exception as e:
            log.debug("Temperature convert: {}".format(e))
            return None

        X1 = ((UT - self._clb["AC6"]) * self._clb["AC5"]) >> 15
        X2 = (self._clb["MC"] << 11) / (X1 + self._clb["MD"])
        self._raw["B5"] = int(X1 + X2)
        temp = ((self._raw["B5"] + 8) >> 4) / 10.0

        # X1 = (UT-self._AC6)*self._AC5/2**15
        # X2 = self._MC*2**11/(X1+self._MD)
        # self.B5_raw = X1+X2
        # temp = (((X1+X2)+8)/2**4)/10

        log.debug("Temperature: {} .C".format(temp))
        return temp


    def _pressure(self):
        '''
        Pressure in mbar.
        '''

        try:
            MSB = unp('B', self._raw["MSB"])[0]
            LSB = unp('B', self._raw["LSB"])[0]
            XLSB = unp('B', self._raw["XLSB"])[0]
            B5_raw = self._raw["B5"]
        except Exception as e:
            log.debug("Pressure convert: {}".format(e))
            return None

        if B5_raw:

            UP = ((MSB << 16) + (LSB << 8) + XLSB) >> (8 - self.oversample_setting)
            B6 = B5_raw - 4000
            X1 = (self._clb["B2"] * (B6 ** 2 / 2 ** 12)) / 2 ** 11
            X2 = self._clb["AC2"] * B6 / 2 ** 11
            X3 = X1 + X2
            B3 = ((int((self._clb["AC1"] * 4 + X3)) << self.oversample_setting) + 2) / 4
            X1 = self._clb["AC3"] * B6 / 2 ** 13
            X2 = (self._clb["B1"] * (B6 ** 2 / 2 ** 12)) / 2 ** 16
            X3 = ((X1 + X2) + 2) / 2 ** 2
            B4 = abs(self._clb["AC4"]) * (X3 + 32768) / 2 ** 15
            B7 = (abs(UP) - B3) * (50000 >> self.oversample_setting)
            if B7 < 0x80000000:
                pressure = (B7 * 2) / B4
            else:
                pressure = (B7 / B4) * 2
            X1 = (pressure / 2 ** 8) ** 2
            X1 = (X1 * 3038) / 2 ** 16
            X2 = (-7357 * pressure) / 2 ** 16

            p_pressure = pressure + (X1 + X2 + 3791) / 2 ** 4

            log.debug("Pressure: {} mbar".format(p_pressure))

            return p_pressure

        return None


    def _altitude(self):
        '''
        Altitude in m.
        '''
        try:
            alt = -7990.0 * math.log(self.pressure / self.baseline)
        except Exception as e:
            log.debug("Pressure convert: {}".format(e))
            return None

        log.debug("Altitude: {}".format(alt))

        return alt

    def set_callback(self, f):
        self.cb = f



    def dataldump(self):
        return [self.temperature, self.pressure, self.altitude]


    async def _run(self):
        log.info("Coro Run")
        while True:

            if self.status == 0:
                self.temperature = False
                self.pressure = False
                self.altitude = False
                self.sensor_detect()
                await asyncio.sleep(5)
            else:

                raw_data = await self._get_data()

                if raw_data:

                    self.temperature = self._temperature()
                    self.pressure = self._pressure()
                    self.altitude = self._altitude()

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

