
from machine import Pin
import time
import relay


class PinButton:
    '''
    B
    '''

    # init
    def __init__(self, pinNum, Pull, debug=False, relay_control=None):

        self._pin = Pin(pinNum, Pin.IN, Pull )

        self.debug = debug
        self.status = 0

        self.value = None
        self._value = None

        self.relay = relay.RELAY(relay_control)
        self.button = None

    def makebutton(self):

        delays = -20  # mS delay

        while True:

                self._value = self._pin.value()
                t_start = time.ticks_ms()
                self.status = 1

                if self._value == 0:
                    while time.ticks_diff(t_start, time.ticks_ms()) <= delays:
                        self.status = 10
                        yield None

                    self.relay.save_state()
                    self.value = self._value
                    self.status = 1

                    #self.relay.set_state(1)
                    #self.value = self._value
                    #self.status = 11
                # else:
                #     self.value = 1
                #     self.relay.set_state(0)
                #     self.status = 12


                yield None

    def start(self):

        self.button = self.makebutton()  # Generator instance
        next(self.button)

    def stop(self):

        self.button = None  # Generator instance




    @property
    def push(self):
        '''
        T
        '''
        try:
            next(self.button)
        except StopIteration:
            if self.debug:
                print("StopIteration")
            return -255

        value = self.value
        if self.status == 0:
            value = -1

        return value







