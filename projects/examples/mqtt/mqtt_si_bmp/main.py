import machine
from machine import Timer
import time
from simple import MQTTClient
import ubinascii
import bmp180
import si7021
from machine import I2C, Pin, PWM

tim1 = Timer(-1)
tim2 = Timer(-1)
tim3 = Timer(-1)


client_id = b"esp8266_" + ubinascii.hexlify(machine.unique_id())

# "broker": '192.168.2.138',
# "broker": 'iot.eclipse.org',

CONFIG = {
    "broker": 'iot.eclipse.org',
    "port" : 1883,
    "sensor_pin": 0,
    "client_id": client_id,
    "topic": b"devices/"+client_id+"/#",
    "BMP_T" : b"devices/"+client_id+"/BMP180/Temperature",
    "BMP_P" : b"devices/"+client_id+"/BMP180/Pressure",
    "SI_T" : b"devices/"+client_id+"/SI7021/Temperature",
    "SI_H" : b"devices/"+client_id+"/SI7021/Humidity",
    "ping" : b"devices/"+client_id+"/ping",

}


def load_config():
    import ujson as json
    try:
        with open("/config.json") as f:
            config = json.loads(f.read())
    except (OSError, ValueError):
        print("Couldn't load /config.json")
        save_config()
    else:
        CONFIG.update(config)
        print("Loaded config from /config.json")

def save_config():
    import ujson as json
    try:
        with open("/config.json", "w") as f:
            f.write(json.dumps(CONFIG))
    except OSError:
        print("Couldn't save /config.json")


def setup():

    i2c = I2C(Pin(5), Pin(4))

    global sensor_bmp
    sensor_bmp = bmp180.BMP180(i2c, debug=False)

    global sensor_si
    sensor_si = si7021.SI7021(i2c, debug=False)

    global pwm2
    pwm2 = PWM(Pin(2), freq=2, duty=512)

    global MESSAGES

    MESSAGES = {
        'BMP_T': None,
        'BMP_P': None,
        'SI_T': None,
        'SI_H': None,
    }


    global publish
    publish = make_publish()


def make_publish():


    while True:
        print("INF: Start Publish")

        for key, value in MESSAGES.items():
            t_start = time.ticks_ms()

            while time.ticks_diff(t_start, time.ticks_ms()) <= 2000:  # 2000mS delay
                yield None

            print("INF: Pub: %s, %s" % (key, value))
            if c_mqtt and c_mqtt.status == 1 and value:
                c_mqtt.publish(CONFIG[key], bytes(value, 'utf-8'))

        while time.ticks_diff(t_start, time.ticks_ms()) <= 15000:  # 15000mS delay
            yield None


        yield True


def sub_cb(topic, msg):

    print(topic, msg)


def config_mqtt_client():
    global c_mqtt
    c_mqtt = MQTTClient(CONFIG['client_id'], CONFIG['broker'], CONFIG['port'], timeout=1, sbt=CONFIG['topic'], debug=False )
    # Subscribed messages will be delivered to this callback
    c_mqtt.set_callback(sub_cb)



def check():

    if c_mqtt and c_mqtt.status == 0:
        c_mqtt.con2()

    global MESSAGES
    MESSAGES = {
        'BMP_T': str(sensor_bmp.temperature),
        'BMP_P': str(sensor_bmp.pressure),
        'SI_T': str(sensor_si.temperature),
        'SI_H': str(sensor_si.humidity),
    }



def wait_msg():

    if c_mqtt and c_mqtt.status == 1:
        c_mqtt.wait_msg()




def pubm():

    next(publish)

    # bmp_temperature = sensor_bmp.temperature
    # bmp_pressure = sensor_bmp.pressure
    #
    # print("BMP C: %f" % bmp_temperature)
    # print("BMP PH: %f" % bmp_pressure)
    #
    # si_temperature = sensor_si.temperature
    # si_humidity = sensor_si.humidity
    #
    # print("SI C: %f" % si_temperature)
    # print("SI H: %f" % si_humidity)
    #
    # if c_mqtt and c_mqtt.status == 1:
    #
    #     # c_mqtt.publish(b"devices/"+client_id+"/BMP180/Temperature",bytes(str("23.5"),'utf-8'))
    #
    #     c_mqtt.publish(CONFIG['BMP_T'], bytes(str(bmp_temperature), 'utf-8'))
    #     c_mqtt.publish(CONFIG['BMP_P'], bytes(str(bmp_pressure), 'utf-8'))
    #     c_mqtt.publish(CONFIG['SI_T'], bytes(str(si_temperature), 'utf-8'))
    #     c_mqtt.publish(CONFIG['SI_H'], bytes(str(si_humidity), 'utf-8'))


def run_timer():



    tim1.init(period=15000, mode=Timer.PERIODIC, callback=lambda t: check())
    tim2.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: wait_msg())
    tim3.init(period=5000, mode=Timer.PERIODIC, callback=lambda t: pubm())

    # tim1.init(period=10000, mode=Timer.ONE_SHOT, callback=lambda t: connect_mqtt_client())


def main():

    config_mqtt_client()
    run_timer()


if __name__ == '__main__':
    load_config()
    setup()
    main()
