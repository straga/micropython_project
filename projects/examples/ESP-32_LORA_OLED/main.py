import machine
from machine import Timer
import si7021
from machine import I2C, Pin, PWM

tim3 = Timer(3)
tim2 = Timer(2)



# OLED 128x64
import ssd1306



def setup():

    #OLED RESET PIN
    pin16 = machine.Pin(16, machine.Pin.OUT)
    pin16.value(1)

    #i2c = I2C(Pin(5), Pin(4)) #ESP8266 - ESP32 DEVKIT
    i2c = I2C(sda=Pin(4), scl=Pin(15))

    global sensor_si
    sensor_si = si7021.SI7021(i2c, debug=True)

    global display
    display = ssd1306.SSD1306_I2C(128, 64, i2c)

    display.fill(0)
    display.text('HELLO', 0, 10)
    display.show()

    global ping
    ping = ""

    global si_temperature
    si_temperature = -251
    global si_humidity
    si_humidity = -251

    global pwm2
    #pwm2 = PWM(Pin(2), freq=2, duty=512) #ESP8266 - ESP32 DEVKIT
    pwm2 = PWM(Pin(25), freq=2, duty=512) #ESP32+LORA+OLED



def pubm():
    global si_temperature
    si_temperature = sensor_si.temperature

    global si_humidity
    si_humidity = sensor_si.humidity

    print(si_temperature)
    print(si_humidity)


def oled_status():

    global ping
    if ping == "":
        ping = "o"
    else:
        ping = ""

    global display
    display.fill(0)
    display.text(ping, 115, 10)
    display.text('T:' + str(si_temperature), 0, 10)
    display.text('H:' + str(si_humidity), 0, 20)
    display.show()


def run_timer():

    tim3.init(period=10000, mode=Timer.PERIODIC, callback=lambda t: pubm())
    tim2.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: oled_status())


def main():
    run_timer()


if __name__ == '__main__':
    setup()
    main()
