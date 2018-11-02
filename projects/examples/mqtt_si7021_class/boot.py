# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
#import webrepl
#webrepl.start()
import time
import network
import gc

gc.enable()

print("will run main Runner in 3 sec")
time.sleep(3)
import metaclass