'''
SI7021 is a micropython module for the SI7021 sensor. It measures
Temperature as well as Humidity.
'''

from ustruct import unpack as unp
import ustruct
import math
import time


class SI7021:

    __I2C_ADDR = 0x40

    #I2C commands
    __RH_READ            = 0xE5
    __TEMP_READ          = 0xE3
    __POST_RH_TEMP_READ  = 0xE0
    __RESET              = 0xFE
    __USER1_READ         = 0xE7
    __USER1_WRITE        = 0xE6
    __CRC8_POLYNOMINAL   = 0x13100 # CRC8 polynomial for 16bit CRC8 x^8 + x^5 + x^4 + 1
    TRIGGER_TEMP_MEASURE_HOLD   = 0xE3
    TRIGGER_HUMD_MEASURE_HOLD   = 0xE5
    TRIGGER_TEMPERATURE_NO_HOLD = 0xF3
    TRIGGER_HUMIDITY_NO_HOLD    = 0xF5


    '''
    Module for the SI7021 sensor.
    '''

    # init
    def __init__(self, i2c, address=__I2C_ADDR, debug=False):

        self.i2c = i2c
        self.si_addr = address
        self.debug = debug
        self.si_exists = False
        self.status = 0

        self.T_raw = None
        self.H_raw = None

        self.gauge = self.makegauge() # Generator instance
        for _ in range(128):
            next(self.gauge)
            time.sleep_ms(1)

    def read_user_register(self):
    # Read the user register byte
        reg = None
        try:
            reg = self.i2c.readfrom_mem(self.si_addr, self.__USER1_READ, 1)
        except OSError as e:
            self.status = 0
            self.soft_reset()
            if self.debug:
                print("Sensor Error or not present: %s" % e)
            return 0

        self.status = 1

        if self.debug:
            print("Sensor present / Register Byte: %s" % reg)
        return self.status

    def soft_reset(self):
    # Soft Reset
        try:
            self.i2c.writeto(self.si_addr, ustruct.pack('b', self.__RESET))
        except OSError as e:
            return None
        return 1

    def makegauge(self):
        '''
        Generator refreshing the raw measurments.
        time.sleep(1)           # sleep for 1 second
        time.sleep_ms(500)      # sleep for 500 milliseconds
        time.sleep_us(10)       # sleep for 10 microseconds
        start = time.ticks_ms() # get millisecond counter
        delta = time.ticks_diff(start, time.ticks_ms()) # compute time difference
        '''
        delays = -25  # mS delay

        while True:

            if self.status == 0 or self.status > 1:
                self.read_user_register()
                yield None
            else:

                #TEMPERATURE_NO_HOLD
                try:
                    self.i2c.writeto(self.si_addr, ustruct.pack('b', self.TRIGGER_TEMPERATURE_NO_HOLD))
                except OSError:
                    self.status = 12
                    yield None

                t_start = time.ticks_ms()
                while time.ticks_diff(t_start, time.ticks_ms()) >= delays:
                    yield None
                try:
                    self.T_raw = self.i2c.readfrom(self.si_addr, 3)
                except:
                    self.status = 13
                    yield None

                #HUMIDITY_NO_HOLD
                try:
                    self.i2c.writeto(self.si_addr, ustruct.pack('b', self.TRIGGER_HUMIDITY_NO_HOLD))
                except OSError:
                    self.status = 22
                    yield None

                t_start = time.ticks_ms()
                while time.ticks_diff(t_start, time.ticks_ms()) >= delays:
                    yield None
                try:
                    self.H_raw = self.i2c.readfrom(self.si_addr, 3)
                except:
                    self.status = 23
                    yield None

                yield True


    @property
    def temperature(self):
        '''
        Temperature in degree C.
        '''
        try:
            next(self.gauge)
        except StopIteration:
            if self.debug:
                print("StopIteration")
            return -255

        value = self.T_raw
        if self.status == 0:
            value = 0

        if not self.crc8check(value):
            if self.debug:
                print("crc8check: %s" % value)
            return -255

        raw_temp = (value[0] << 8) + value[1]

        raw_temp = raw_temp & 0xFFFC  # Clear the status bits

        # Calculate the actual temperature
        actual_temp = -46.85 + (175.72 * raw_temp / 65536)

        return actual_temp

    @property
    def humidity(self):
        '''
        Temperature in RH.
        '''

        try:
            next(self.gauge)
        except StopIteration:
            return -255

        value = self.H_raw

        if self.status == 0:
            value = 0

        if not self.crc8check(value):
            return -255

        rawRHData = (value[0] << 8) + value[1]

        rawRHData = rawRHData & 0xFFFC;  # Clear the status bits

        # Calculate the actual RH
        actualRH = -6 + (125.0 * rawRHData / 65536)

        return actualRH



    def crc8check(self, value):
        # Calulate the CRC8 for the data received
        # from https://github.com/sparkfun/HTU21D_Breakout
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


