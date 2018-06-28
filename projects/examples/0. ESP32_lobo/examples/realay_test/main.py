

import machine, _thread
from machine import Pin
from button_control import ButtonControl
from runner import Runner

_debug = True
_message = "Run in DEBUG . B4 Control Pin"

#BUTTON CHECK
def button_push_check():

    while True:
        b4.push_check
        _thread.wait(200)

b4_pin = Pin(4, Pin.IN, Pin.PULL_UP)
b4 = ButtonControl(name="B4", _pin=b4_pin, debug=True, on_value=0, off_value=1)
b4.start()
_ = _thread.stack_size(6*1024)
th1 = _thread.start_new_thread("THRD_B4", button_push_check, ())

def main():
    if _debug:
        print("Main = %s" % _message)

    if b4.state != "ON":
        print("START = %s" % "Runner")
        r1 = Runner(name="r1", debug=True, control_pin=b4, control_thread=th1)

    else:
        print("STOP = %s" % "Runner")




if __name__ == '__main__':
    main()
