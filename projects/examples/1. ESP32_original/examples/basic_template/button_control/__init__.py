#
# ver 06.24.18
# Copyright (c) 2018 Viktor Vorobjov
# see:
#       examples\touch_switch_test
#       Holtek - Touch I/O Flash MCU BS83A02A-4/BS83A04A-3/BS83A04A-4

#       examples\button_switch_test
#       Mechanical Pin button
#       Touch pin button - TTP223
#
import uasyncio as asyncio

class ButtonControl:


    def __init__(self, name=None, _pin=False, debug=False, on_value=1, off_value=0,
                 state_on="ON", state_off="OFF"):

        self._switch = _pin
        self.name = name
        self.debug = debug

        self.button = None

        self.on_value = on_value
        self.off_value = off_value

        self.state_on = state_on
        self.state_off = state_off

        self._value = off_value

        self.cb = None

        self.change_state()

        self.debounce_ms = 300

        loop = asyncio.get_event_loop()
        loop.create_task(self.push_check())



    def change_state(self):
        self._value = self._switch.value()

        if self._value == self.on_value:
            self.state = self.state_on
        elif self._value == self.off_value:
            self.state = self.state_off

        if self.cb:
            self.cb()

    async def push_check(self):
        while True:
            if self._switch.value() != self._value:
                self.change_state()
            await asyncio.sleep_ms(self.debounce_ms)


    def set_callback(self, f):
        self.cb = f






