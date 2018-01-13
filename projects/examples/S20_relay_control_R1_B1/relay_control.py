
from machine import Pin
from machine import Pin, PWM

# pwm2 = PWM(Pin(12), freq=100, duty=1000)


class RELAY:
    '''
    Relay Control with state
    '''

    # init
    def __init__(self, name = None, pin_num = None, on_value=0,):
        self._relay = PWM(Pin(pin_num), freq=100, duty=on_value)
        self.on_value = on_value
        self.save_state = False
        self.state = self.get_state(on_value)
        self.cb = None
        self.name = name


    def set_state(self, reguest_value):
        self._relay.duty(reguest_value)
        self.state = self.get_state()
        if self.cb:
           self.cb(self)

    def get_state(self, value = None):

        if not value:
            value = self._relay.duty()

        if self.on_value == value:
            return  "ON"
        else:
            return  "OFF"

    def change_state(self):

        if self._relay.duty() > 1000:
            self._relay.duty(0)
        else:
            self._relay.duty(1024)

        self.state = self.get_state()
        if self.cb:
           self.cb(self)


    def set_callback(self, f):
        self.cb = f










