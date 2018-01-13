#Test for Relay
import machine
RELAYS = [machine.Pin(i, machine.Pin.OUT, value=0) for i in (12, 13)]

RELAYS[0].value(1) #on
RELAYS[1].value(1) #on

RELAYS[0].value(0) #off
RELAYS[1].value(0) #off


import machine
button2 = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
button1 = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)

button1.value()

1 - no push
0 - push