
from machine import Pin
import time

class PinButton:
    '''
    B
    '''

    # init
    def __init__(self, pinNum, Pull, debug=False, relay_control=None, on_value=0):

        self._pin = Pin(pinNum, Pin.IN, Pull )

        self.debug = debug
        self.status = 0

        self.value = "off"
        self._value = None

        self.relay = relay_control
        self.button = None

        self.on_value = on_value


    def makebutton(self):

        delays = -200  # mS delay

        while True:

                t_start = time.ticks_ms()
                self.status = 1

                if self._pin.value() == self.on_value:
                    while time.ticks_diff(t_start, time.ticks_ms()) >= delays:

                        if self.value == "off":
                            if self.relay:
                                self.relay.change_state()
                            self.value = "on"
                            self.status = 1

                        self.status = 10
                        yield None

                else:
                    self.value = "off"


                yield True



    def start(self):

        self.button = self.makebutton()  # Generator start
        next(self.button)

    def stop(self):

        self.button = None  # Generator stop

    @property
    def push(self):
        '''
        T
        '''
        self.status = 0
        try:
            next(self.button)
        except StopIteration:
            if self.debug:
                print("StopIteration")
            return -255

        value = self.status

        return value







