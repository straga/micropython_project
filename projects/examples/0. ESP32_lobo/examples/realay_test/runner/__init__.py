

import machine, _thread
from machine import Pin
from relay_control import RelayControl

class Runner:
    '''

    '''

    # init
    def __init__(self,
                 name=None,
                 debug=False,
                 control_pin=None,
                 control_thread=None
                 ):

        self.control_pin = control_pin
        self.control_thread = control_thread
        self.name = name
        self.debug = debug

        self.led2_setup()

        self.control_pin.set_callback(self.b4_cb)


    #BUTTON CALLBACK

    def b4_cb(self):

        if self.control_pin.state == "ON":
            self.led_2.change_state()

        if self.debug:
            print("Button is = %s" % self.control_pin.state)


    def led2_setup(self):

        LED_2_pin = Pin(2, Pin.INOUT)
        LED_2_on = 1

        self.led_2 = RelayControl(name="Led2", _pin=LED_2_pin, on_value=LED_2_on, default=LED_2_on)
        self.led_2.set_callback(self.relay_cb)



    #RELAY CALLBACK
    def relay_cb(self,relay):

        if self.debug:
            print("Led: %s = %s" % (relay.name, relay.state))
