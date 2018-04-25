# -*- coding: utf-8 -*-
import machine
from machine import Timer
import time
from mqtt_simple import MQTTClient
import ubinascii
from machine import Pin

tim1 = Timer(-1)
tim2 = Timer(-1)
tim3 = Timer(-1)
tim4 = Timer(-1)
tim5 = Timer(-1)

import time
import machine

global debug
debug = False

client_id = b"esp8266_" + ubinascii.hexlify(machine.unique_id())

# "broker": '192.168.2.138',
# "broker": 'iot.eclipse.org'

CONFIG = {
    "broker": '192.168.2.153',
    "port" : 1883,
    "sensor_pin": 0,
    "client_id": client_id,
    "topic": b"devices/"+client_id+"/#",
    "ping" : b"devices/"+client_id+"/ping",
    "sw1_set" : b"devices/"+client_id+"/sw1/set",
    "sw1_state" : b"devices/"+client_id+"/sw1/state",
    "sw2_set": b"devices/" + client_id + "/sw2/set",
    "sw2_state": b"devices/" + client_id + "/sw2/state",
    "DS18B20" : b"devices/" + client_id + "/18b20",

}

on = 1
off = 0

RELAYS = [machine.Pin(i, machine.Pin.OUT, value=off) for i in (12, 13)]
relay1 = 1
relay2 = 0

but1_pin = 2
but2_pin = 0
button1 = machine.Pin(but1_pin, machine.Pin.IN, machine.Pin.PULL_UP)
button2 = machine.Pin(but2_pin, machine.Pin.IN, machine.Pin.PULL_UP)


def get_value_h(value):

    if value == 0:
        return "OFF"
    if value == 1:
        return "ON"
    return None

def get_relay_h(value):

    if value == 0:
        return "Relay 2"
    if value == 1:
        return "Relay 1"
    return None


def get_relays():
    return RELAYS

def get_relay_status(relay):
    value = RELAYS[int(relay)].value()
    result = get_value_h(value)

    print("%s status: %s" % (get_relay_h(relay), result))
    return value

def set_relay_status(relay, value):
    RELAYS[int(relay)].value(int(value))
    global MESSAGES

    if relay == relay2:

        MESSAGES['sw2_state'] = get_value_h(value)

    if relay == relay1:

        MESSAGES['sw1_state'] = get_value_h(value)

    print("%s set to %s" % (get_relay_h(relay), get_value_h(value)))


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

        to_mqtt = get_messages()

        if debug:
            print("Message to MQTT", to_mqtt)

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

        yield True


def sub_cb(topic, msg):

    if topic.decode() == CONFIG['sw2_set']:

        if msg.decode() == "ON":
            set_relay_status(relay2, on)

        if msg.decode() == "OFF":
            set_relay_status(relay2, off)

    if topic.decode() == CONFIG['sw1_set']:

        if msg.decode() == "ON":
            set_relay_status(relay1, 1)

        if msg.decode() == "OFF":
            set_relay_status(relay1, 0)

    if debug:
        print(topic, msg)


def config_mqtt_client():
    global c_mqtt

    try:
        c_mqtt = MQTTClient(CONFIG['client_id'], CONFIG['broker'], CONFIG['port'], timeout=1, sbt=CONFIG['topic'], debug=False)
        c_mqtt.set_callback(sub_cb)
    except (OSError, ValueError):
        print("Couldn't connect to MQTT")




def check():

    if c_mqtt and c_mqtt.status == 0:
        c_mqtt.con2()

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


def switch_relay(relay):
    if get_relay_status(relay):
        set_relay_status(relay, off)
    else:
        set_relay_status(relay, on)

global last_interrupt_time
last_interrupt_time = 0

def button_callback(pin):

    global last_interrupt_time
    interrupt_time = time.ticks_ms()

    sw1 = Pin(but1_pin)
    sw2 = Pin(but2_pin)

    if time.ticks_diff(last_interrupt_time, interrupt_time) <= -600:

        if pin is sw1:
            switch_relay(relay1)
        elif pin is sw2:
            switch_relay(relay2)

    last_interrupt_time = interrupt_time





def main():

    config_mqtt_client()
    run_timer()

    button1.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_callback)
    button2.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_callback)



if __name__ == '__main__':
    load_config()
    setup()
    main()
