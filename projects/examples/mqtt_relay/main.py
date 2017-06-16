# -*- coding: utf-8 -*-
import machine
from machine import Timer
import time
from simple import MQTTClient
import ubinascii
from machine import Pin, PWM

tim1 = Timer(-1)
tim2 = Timer(-1)
tim3 = Timer(-1)
tim4 = Timer(-1)
tim5 = Timer(-1)

import time
import machine



global debug
debug = False

global tem1
tem1 = False

global r1_manual
global r2_manual

r1_manual = False
r2_manual = False

client_id = b"esp8266_" + ubinascii.hexlify(machine.unique_id())

# "broker": '192.168.2.138',
# "broker": 'iot.eclipse.org'

CONFIG = {
    "broker": '192.168.2.138',
    "port" : 1883,
    "sensor_pin": 0,
    "client_id": client_id,
    "topic": b"devices/"+client_id+"/#",
    "ping" : b"devices/"+client_id+"/ping",
    "sw1_set" : b"devices/"+client_id+"/sw1/set",
    "sw1_state" : b"devices/"+client_id+"/sw1/state",
    "sw2_set": b"devices/" + client_id + "/sw2/set",
    "sw2_state": b"devices/" + client_id + "/sw2/state",

}

RELAYS = [machine.Pin(i, machine.Pin.OUT, value=1) for i in (4, 5)]

def get_value_h(value):

    if value == 1:
        return "OFF"
    if value == 0:
        return "ON"
    return None



def get_relays():
    return RELAYS

def get_relay_status(relay):
    value = RELAYS[int(relay)].value()
    result = get_value_h(value)

    return "Relay %s status: %s" % (relay, result)


def set_relay_status(relay, value):
    RELAYS[int(relay)].value(int(value))
    global MESSAGES

    if relay == 1:

        MESSAGES['sw2_state'] = get_value_h(value)

    if relay == 0:

        MESSAGES['sw1_state'] = get_value_h(value)

    return "Relay %s set to %s" % (relay, value)


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


    global pwm2
    pwm2 = PWM(Pin(2), freq=2, duty=512)

    set_messages()

    global publish
    publish = make_publish()

    global roms
    roms = False



def get_messages():
    return MESSAGES

def set_messages():

    global MESSAGES
    MESSAGES = {
        # 'wait_msg' : '1'
    }

def clear_messages(key):

    global MESSAGES
    MESSAGES[key] = None



def make_publish():


    while True:
        # print("INF: Start Publish")

        to_mqtt = get_messages()

        # if debug:
        #     print("Message to MQTT", to_mqtt)

        if to_mqtt:

            for key, value in to_mqtt.items():
                t_start = time.ticks_ms()

                if value:

                    while time.ticks_diff(t_start, time.ticks_ms()) <= -2000:  # 2000mS delay
                        yield None
                    if debug:
                        print("Message Ready: Pub: %s, %s" % (key, value))
                    if c_mqtt and c_mqtt.status == 1:

                        retain = False

                        if key == 'sw2_state' or  key == 'sw1_state':

                            retain = True

                        result = c_mqtt.publish(CONFIG[key], bytes(value, 'utf-8'), retain)
                        if result == 1:
                            clear_messages(key)
                        if debug:
                            print("Result pub to MQTT", result)
                        # if key == 'wait_msg':
                        #     c_mqtt.wait_msg()

        yield True


def sub_cb(topic, msg):
    global r1_manual
    global r2_manual

    if topic.decode() == CONFIG['sw2_set']:

        if msg.decode() == "ON":
            r2_manual = True
            #set_relay_status(1, 0)

        if msg.decode() == "OFF":
            r2_manual = False
            #set_relay_status(1, 1)

    if topic.decode() == CONFIG['sw1_set']:

        if msg.decode() == "ON":
            r1_manual = True
            #set_relay_status(0, 0)

        if msg.decode() == "OFF":
            r1_manual = False
            #set_relay_status(0, 1)

    if debug:
        print(topic, msg)


def config_mqtt_client():
    global c_mqtt

    try:
        c_mqtt = MQTTClient(CONFIG['client_id'], CONFIG['broker'], CONFIG['port'], timeout=1, sbt=CONFIG['topic'], debug=False)
        c_mqtt.set_callback(sub_cb)
    except (OSError, ValueError):
        print("Couldn't connect to MQTT")

    # Subscribed messages will be delivered to this callback



def check():

    if c_mqtt and c_mqtt.status == 0:

        global r2_manual
        global r1_manual

        set_relay_status(1, 1)
        set_relay_status(0, 1)
        r1_manual = False
        r1_manual = False

        c_mqtt.con2()

    else:

        if r2_manual:
            set_relay_status(1, 0)
        else:
            set_relay_status(1, 1)

        if r1_manual:
            set_relay_status(0, 0)
        else:
            set_relay_status(0, 1)


    global MESSAGES
    MESSAGES['ping'] = '1'


def wait_msg():

    if c_mqtt and c_mqtt.status == 1:
        c_mqtt.wait_msg()


def pubm():

    next(publish)


def run_timer():


    tim1.init(period=15000, mode=Timer.PERIODIC, callback=lambda t: check())
    tim2.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: wait_msg())
    tim3.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: pubm())


    # tim5.init(period=60000, mode=Timer.PERIODIC, callback=lambda t: get_relay_status(1))
    # tim1.init(period=10000, mode=Timer.ONE_SHOT, callback=lambda t: connect_mqtt_client())


def main():

    config_mqtt_client()
    run_timer()


if __name__ == '__main__':
    load_config()
    setup()
    main()
