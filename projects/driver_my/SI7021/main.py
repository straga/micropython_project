import machine
from machine import Timer
import si7021
from machine import I2C, Pin, PWM

tim1 = Timer(-1)
tim2 = Timer(-1)
tim3 = Timer(-1)



def setup():

    #i2c = I2C(Pin(5), Pin(4)) #ESP8266 - ESP32 DEVKIT
    i2c = I2C(sda=Pin(4), scl=Pin(5)) #Wemos D1: pin4=D2, pin5=D1

    global sensor_si
    sensor_si = si7021.SI7021(i2c, debug=True)

    global pwm2
    pwm2 = PWM(Pin(2), freq=2, duty=512) #ESP8266 - ESP32 DEVKIT
    #pwm2 = PWM(Pin(25), freq=2, duty=512) #ESP32+LORA+OLED



def pubm():

    si_temperature = sensor_si.temperature
    si_humidity = sensor_si.humidity

    print(si_temperature)
    print(si_humidity)


def run_timer():

    tim3.init(period=10000, mode=Timer.PERIODIC, callback=lambda t: pubm())
    # tim1.init(period=10000, mode=Timer.ONE_SHOT, callback=lambda t: connect_mqtt_client())


def main():
    run_timer()


if __name__ == '__main__':
    setup()
    main()
