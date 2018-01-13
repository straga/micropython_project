from machine import Timer
from machine import Pin
import onewire, ds18x20


#Electro Dragon 14 pin
data_pin = Pin(14)

# create the onewire object
ds_1 = ds18x20.DS18X20(onewire.OneWire(data_pin))


#Scan sensors
roms = ds_1.scan()
print("ROMS: %s" % (roms))
ds_1.convert_temp()
ds_1.read_temp(roms[0])