import machine
from machine import Pin
from relay_control import RELAY
from button_control import TouchButton

from machine import Timer

#Timer
tim5 = Timer(-1)


#Wemos D1 mini
#Led
LED_2_pin = 2
LED_2 = RELAY(name="Led2", pin_num=LED_2_pin, on_value=0, off_value=1, state_on=1, state_off=0, default=1)


#BUTTON
button_pin = 4

b4 = TouchButton(name="Led2", pin_num=button_pin, pull=Pin.PULL_UP, debug=True, relay_control=LED_2, on_value=1 )
b4.start()


#BUTTON CHECK
def button_push_check():
    b4.push_check




def run_timer():
    tim5.init(period=300, mode=Timer.PERIODIC, callback=lambda t: button_push_check())

def main():
    run_timer()

if __name__ == '__main__':
    main()