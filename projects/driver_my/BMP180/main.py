import machine
from machine import Timer
import bmp180
from machine import I2C, Pin, PWM

tim1 = Timer(-1)
tim2 = Timer(-1)
tim3 = Timer(-1)



def setup():

    i2c = I2C(Pin(5), Pin(4))

    global sensor_bmp
    sensor_bmp = bmp180.BMP180(i2c, debug=True)

    global pwm2
    pwm2 = PWM(Pin(2), freq=2, duty=512)



def pubm():
    bmp_temperature = sensor_bmp.temperature
    bmp_pressure = sensor_bmp.pressure

    print(bmp_temperature)
    print(bmp_pressure)


def run_timer():

    tim3.init(period=10000, mode=Timer.PERIODIC, callback=lambda t: pubm())
    # tim1.init(period=10000, mode=Timer.ONE_SHOT, callback=lambda t: connect_mqtt_client())


def main():
    run_timer()


if __name__ == '__main__':
    setup()
    main()
