from machine import Pin
p = Pin(26, mode=Pin.OUT, pull=Pin.PULL_UP)
p.value(1)
print("P26 = {} ".format(p.value()))