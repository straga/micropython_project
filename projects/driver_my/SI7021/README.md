Micropython 1.9.3

HTU21D, SI7021 - tested ESP32



I2c test
from machine import I2C, Pin
from ustruct import unpack as unp
import ustruct

i2c = I2C(-1, sda=Pin(4), scl=Pin(5))
i2c.readfrom_mem(0x40, 0xE7, 1)

i2c.writeto(0x40, ustruct.pack('b', 0xF3))
i2c.readfrom(0x40, 3)


