
from machine import Pin

class RELAY:
    '''
    Relay Control with state
    '''

    # init
    def __init__(self, name = None, pin_num = None, on_value=1, off_value=0, state_on="ON", state_off="OFF", default = 0):
        self._relay = Pin(pin_num, Pin.OUT)
        self.on_value = on_value
        self.off_value = off_value
        self.cb = None
        self.name = name
        self.state_on = state_on
        self.state_off = state_off
        self.set_state(default)
        self.state = self.get_state()

    def save_state(self):
        self.state = self.get_state()
        if self.cb:
           self.cb(self)

    def set_state(self, reguest_value):
        self._relay.value(reguest_value)
        self.save_state()

    def get_state(self):

        if self.on_value == self._relay.value():
            return  self.state_on
        else:
            return  self.state_off

    def change_state(self):

        if self._relay.value() == 1:
            self._relay.value(0)
        else:
            self._relay.value(1)

        self.save_state()


    def set_callback(self, f):
        self.cb = f










