
from machine import Pin
import time

class TouchButton:
    '''
    B
    '''

    # init
    def __init__(self, name=None, pin_num=False, pull=False, debug=False, relay_control=None, on_value=1, off_value=0, state_on="ON", state_off="OFF"):

        self._switch = Pin(pin_num, Pin.IN, pull)
        self.name = name
        self.debug = debug
        self.status = 0

        self.relay = relay_control
        self.button = None

        self.on_value = on_value
        self.off_value = off_value

        self.state_on = state_on
        self.state_off = state_off

        self.state = state_off

        self._value = off_value

        self.cb = None



    def change_state(self):

        self._value = self._switch.value()

        if self._value == self.on_value:
            self.state = self.state_on
        elif self._value == self.off_value:
            self.state = self.state_off

        if self.cb:
            self.cb(self)

        self.status = 20



    def makebutton(self):

        while True:

            if self._switch.value() != self._value:

                if self.relay:
                    self.relay.change_state()

                self.change_state()

            self.status = 30

            yield True


    def start(self):

        self.button = self.makebutton()  # Generator start
        next(self.button)

    def stop(self):

        self.button = None  # Generator stop

    @property
    def push_check(self):
        '''
        T
        '''
        self.status = 10
        try:
            next(self.button)
        except StopIteration:
            if self.debug:
                print("StopIteration")
            return -255

        value = self.status

        return value

    def set_callback(self, f):
        self.cb = f






