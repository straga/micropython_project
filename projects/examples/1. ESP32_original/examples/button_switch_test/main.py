

import machine, _thread
from machine import Pin
from relay_control import RelayControl
from button_control import ButtonControl

_debug = True
_message = "run in ... ."

#Led
LED_2_pin = Pin(2, Pin.INOUT)
LED_2_on = 1
LED_2 = RelayControl(name="Led2", _pin=LED_2_pin, on_value=LED_2_on, default=1-LED_2_on)

#BUTTON

b4_pin = Pin(4, Pin.IN, Pin.PULL_UP)


b4 = ButtonControl(name="B4", _pin=b4_pin, debug=True, on_value=1, off_value=0) #Holtek - BS83A02A-4 , Active VCC, default Gnd

def b4_cb():

    if b4.state == "ON":
        LED_2.change_state(LED_2_on)
    else:
        LED_2.change_state(1-LED_2_on)

    if _debug:
        print("Button is = %s" % b4.state)
        print("Led is  = %s" % LED_2.state)



# #BUTTON CHECK
def button_push_check():

    while True:
        b4.push_check
        _thread.wait(200)


def main():
    if _debug:
        print("Main = %s" % _message)

    b4.start()
    b4.set_callback(b4_cb)

    th1 = _thread.start_new_thread("THRD_B4", button_push_check, ())


if __name__ == '__main__':
    main()
