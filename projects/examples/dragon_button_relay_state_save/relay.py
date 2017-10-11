
from machine import Pin

class RELAY:
    '''
    B
    '''

    # init
    def __init__(self, pin_num, d_value=0):
        self._relay = Pin(pin_num, Pin.OUT, d_value )

    def set_state(self, reguest_value):
        self._relay.value(reguest_value)


    def save_state(self):

        if self._relay.value() == 1:
            self._relay.value(0)
        else:
            self._relay.value(1)








