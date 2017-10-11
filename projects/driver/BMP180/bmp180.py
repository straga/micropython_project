'''
bmp180 is a micropython module for the Bosch BMP180 sensor. It measures
temperature as well as pressure, with a high enough resolution to calculate
altitude.
'''

from ustruct import unpack as unp
import ustruct
import math
import time

# BMP180 class
class BMP180:


    __BMP180_READPRESSURECMD = 0x34
    __BMP180_READTEMPCMD = 0x2E
    __BMP180_CONTROL = 0xF4

    '''
    Module for the BMP180 pressure sensor.
    '''

    # 119 adress of BMP180 is hardcoded on the sensor

    # init
    def __init__(self, i2c, address=119, debug=False):

        self.i2c = i2c
        self._bmp_addr = address
        self.debug = debug
        self.status = 0

        # # self.chip_id = self.i2c.readfrom_mem(self._bmp_addr,0xD0, 1) #chip id adress 0xD0 = always /x55
        #
        #
        # # read calibration data from EEPROM
        self._AC1 = None
        self._AC2 = None
        self._AC3 = None
        self._AC4 = None
        self._AC5 = None
        self._AC6 = None
        self._B1 = None
        self._B2 = None
        self._MB = None
        self._MC = None
        self._MD = None

        # settings to be adjusted by user
        self.oversample_setting = 3
        self.baseline = 101325.0

        # output raw
        self.UT_raw = None
        self.B5_raw = None
        self.MSB_raw = None
        self.LSB_raw = None
        self.XLSB_raw = None
        self.gauge = self.makegauge() # Generator instance
        for _ in range(128):
            next(self.gauge)
            time.sleep_ms(1)
        #print(self.gauge) 

    def compvaldump(self):
        '''
        Returns a list of all compensation values
        '''
        return [self._AC1, self._AC2, self._AC3, self._AC4, self._AC5, self._AC6, 
                self._B1, self._B2, self._MB, self._MC, self._MD, self.oversample_setting]


    def sensor_detect(self):



        try:
            self.chip_id = self.i2c.readfrom_mem(self._bmp_addr, 0xD0, 1)  # chip id adress 0xD0 = always /x55
        except OSError as e:
            self.status = 0
            if self.debug:
                print("Sensor Error or not present: %s" % e)
            return self.status

        self.status = 1

        # read calibration data from EEPROM
        self._AC1 = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xAA,2))[0]
        self._AC2 = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xAC,2))[0]
        self._AC3 = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xAE,2))[0]
        self._AC4 = unp('>H', self.i2c.readfrom_mem(self._bmp_addr, 0xB0,2))[0]
        self._AC5 = unp('>H', self.i2c.readfrom_mem(self._bmp_addr, 0xB2,2))[0]
        self._AC6 = unp('>H', self.i2c.readfrom_mem(self._bmp_addr, 0xB4,2))[0]
        self._B1 = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xB6,2))[0]
        self._B2 = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xB8,2))[0]
        self._MB = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xBA,2))[0]
        self._MC = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xBC,2))[0]
        self._MD = unp('>h', self.i2c.readfrom_mem(self._bmp_addr, 0xBE,2))[0]

        if self.debug:
            print("Sensor present: %s" % self.status)

        return self.status


    # gauge raw
    def makegauge(self):
        '''
        Generator refreshing the raw measurments.
        time.sleep(1)           # sleep for 1 second
        time.sleep_ms(500)      # sleep for 500 milliseconds
        time.sleep_us(10)       # sleep for 10 microseconds
        start = time.ticks_ms() # get millisecond counter
        delta = time.ticks_diff(start, time.ticks_ms()) # compute time difference
        '''
        delays = (-5, -8, -14, -25)



        while True:

            if self.status == 0:
                self.sensor_detect()
                yield None
            else:

                #TEMP
                try:
                    self.i2c.writeto_mem(self._bmp_addr, self.__BMP180_CONTROL,
                                         ustruct.pack('I', self.__BMP180_READTEMPCMD))
                except OSError as e:
                    print(e)
                    self.status = 0
                    yield None

                t_start = time.ticks_ms()
                while time.ticks_diff(t_start, time.ticks_ms()) >= 5: # 5mS delay
                    yield None
                try:
                    self.UT_raw = self.i2c.readfrom_mem(self._bmp_addr, 0xF6, 2)
                except:
                    yield None

                #PRESSURE
                com_pressure = self.__BMP180_READPRESSURECMD + (self.oversample_setting << 6)
                try:
                    self.i2c.writeto_mem(self._bmp_addr, self.__BMP180_CONTROL, ustruct.pack('I', com_pressure))
                except OSError:
                    self.status = 0
                    yield None


                t_pressure_ready = delays[self.oversample_setting]
                t_start = time.ticks_ms()
                while time.ticks_diff(t_start, time.ticks_ms()) >= t_pressure_ready:
                    yield None
                try:
                    self.MSB_raw = self.i2c.readfrom_mem(self._bmp_addr, 0xF6, 1)
                    self.LSB_raw = self.i2c.readfrom_mem(self._bmp_addr, 0xF7, 1)
                    self.XLSB_raw = self.i2c.readfrom_mem(self._bmp_addr, 0xF8, 1)
                except:
                    yield None
                yield True

    def blocking_read(self):
        if next(self.gauge) is not None: # Discard old data
            pass
        while next(self.gauge) is None:
            pass

    @property
    def oversample_sett(self):
        return self.oversample_setting

    @oversample_sett.setter
    def oversample_sett(self, value):
        if value in range(4):
            self.oversample_setting = value
        else:
            print('oversample_sett can only be 0, 1, 2 or 3, using 3 instead')
            self.oversample_setting = 3

    @property
    def temperature(self):
        '''
        Temperature in degree C.
        '''

        try:
            next(self.gauge)
        except StopIteration:
            return -249

        if self.status == 0:
            return -250

        try:
            UT = unp('>h', self.UT_raw)[0]
        except:
            return -251

        X1 = ((UT - self._AC6) * self._AC5) >> 15
        X2 = (self._MC << 11) / (X1 + self._MD)
        self.B5_raw = int(X1 + X2)
        temp = ((self.B5_raw + 8) >> 4) / 10.0

        # X1 = (UT-self._AC6)*self._AC5/2**15
        # X2 = self._MC*2**11/(X1+self._MD)
        # self.B5_raw = X1+X2
        # temp = (((X1+X2)+8)/2**4)/10

        if self.debug:
            print("DBG: Calibrated temperature = %f C" % temp)
        return temp

    @property
    def pressure(self):
        '''
        Pressure in mbar.
        '''

        try:
            next(self.gauge)
        except StopIteration:
            return -252

        if self.status == 0:
            return -253


        self.temperature  # Populate self.B5_raw
        try:
            MSB = unp('<h', self.MSB_raw)[0]
            LSB = unp('<h', self.LSB_raw)[0]
            XLSB = unp('<h', self.XLSB_raw)[0]
        except:
            return -254
        UP = ((MSB << 16)+(LSB << 8)+XLSB) >> (8-self.oversample_setting)
        B6 = self.B5_raw-4000
        X1 = (self._B2*(B6**2/2**12))/2**11
        X2 = self._AC2*B6/2**11
        X3 = X1+X2
        B3 = ((int((self._AC1*4+X3)) << self.oversample_setting)+2)/4
        X1 = self._AC3*B6/2**13
        X2 = (self._B1*(B6**2/2**12))/2**16
        X3 = ((X1+X2)+2)/2**2
        B4 = abs(self._AC4)*(X3+32768)/2**15
        B7 = (abs(UP)-B3) * (50000 >> self.oversample_setting)
        if B7 < 0x80000000:
            pressure = (B7*2)/B4
        else:
            pressure = (B7/B4)*2
        X1 = (pressure/2**8)**2
        X1 = (X1*3038)/2**16
        X2 = (-7357*pressure)/2**16

        p_pressure = pressure+(X1+X2+3791)/2**4

        if self.debug:
            print("DBG: Pressure = %d Pa" % p_pressure)

        return p_pressure

    @property
    def altitude(self):
        '''
        Altitude in m.
        '''
        try:
            p = -7990.0*math.log(self.pressure/self.baseline)
        except:
            p = -255

        if self.debug:
            print("DBG: Altitude = %d" % (p))
        return p
