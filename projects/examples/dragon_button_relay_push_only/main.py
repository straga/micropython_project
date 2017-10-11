
from machine import Timer
from machine import Pin
import pinButton

b2 = pinButton.PinButton(2, Pin.PULL_UP, debug=True, relay_control=12)
b0 = pinButton.PinButton(0, Pin.PULL_UP, debug=True, relay_control=13)

b0.start()
b2.start()

tim1 = Timer(-1)

def push():

    b0.push
    b2.push

def run_timer():

    tim1.init(period=500, mode=Timer.PERIODIC, callback=lambda t: push())

def main():

    run_timer()

if __name__ == '__main__':
    main()