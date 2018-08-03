# aledflash.py Demo/test program for MicroPython asyncio
# Author: Peter Hinch
# Copyright Peter Hinch 2017 Released under the MIT license
# Flashes the onboard LED's each at a different rate. Stops after ten seconds.
# Run on MicroPython board bare hardware

import uasyncio as asyncio
from mqttse import MQTTClient
from config import load_config, save_config
from machine import Pin, unique_id
import network
import utime
import time
import ubinascii


global CONFIG

global led
global net_fail_count
global net_succ_count
led = Pin(2, Pin.OUT)
net_fail_count = 0
net_succ_count = 0
debug = True


client_id = b"esp8266_" + ubinascii.hexlify(unique_id())
print(client_id)
CONFIG = {
    "broker": '127.0.0.1',
    "port": 1883,
    "sensor_pin": 0,
    "client_id": client_id,
    "topic": b"devices/" + client_id + "/#",
    "ping": b"devices/" + client_id + "/ping",
    "sw1_set": b"devices/" + client_id + "/sw1/set",
    "sw1_state": b"devices/" + client_id + "/sw1/state",
    "sw2_set": b"devices/" + client_id + "/sw2/set",
    "sw2_state": b"devices/" + client_id + "/sw2/state",
}


def setup():
    set_messages()

    global publish
#    publish = make_publish()


def get_messages():
    return MESSAGES


def set_messages():
    global MESSAGES
    MESSAGES = {}


def clear_messages(key):

    global MESSAGES
    MESSAGES[key] = None


async def make_publish():
    while True:
        print("INF: Start Publish")

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
                        result = c_mqtt.publish(
                            CONFIG[key], bytes(value, 'utf-8'), retain)
                        if result == 1:
                            clear_messages(key)
                        if debug:
                            print("Result pub to MQTT", result)
                        # if key == 'wait_msg':
                        #     c_mqtt.wait_msg()

            # yield True
        await asyncio.sleep(1)


def sub_cb(topic, msg):
    global r1_manual
    global r2_manual

    if debug:
        print(topic, msg)


def config_mqtt_client():
    global c_mqtt

    try:
        c_mqtt = MQTTClient(CONFIG['client_id'],
                            CONFIG['broker'], CONFIG['port'])
        c_mqtt.set_callback(sub_cb)
        if debug:
            print("attempt connect to MQTT", str(c_mqtt.status))
    except (OSError, ValueError):
        print("Couldn't connect to MQTT")


async def killer(duration):
    await asyncio.sleep(duration)


async def toggle(objLED, time_ms):
    while True:
        await asyncio.sleep_ms(time_ms)
        objLED.value(not objLED.value())


async def check_connection(delay_secs):
    global net_fail_count
    global net_succ_count
    while True:
        print('Hello')
        sta_if = network.WLAN(network.STA_IF)
        is_connected = sta_if.isconnected()
        if not is_connected:
            net_succ_count = 0
            net_fail_count += 1
            if net_fail_count >= 10:
                reset()
        else:
            net_succ_count += 1
            if net_succ_count >= 5:
                net_fail_count = 0
        if debug:
            print (utime.localtime()[4], ":", utime.localtime()[5],
                   "WIFI is connected: ", is_connected,
                   "Nr times failed:", net_fail_count, net_succ_count)
        await asyncio.sleep(delay_secs)


async def check_mqtt():
    while True:
        if not c_mqtt.status:
            c_mqtt.connect()
        else:
            global MESSAGES
            MESSAGES['ping'] = '1'
            await asyncio.sleep(5)


async def wait_msg():

    if c_mqtt:
        c_mqtt.check_msg()
    await asyncio.sleep(2)


async def pubm():
    if debug:
        print("we are in pubm")
    next(publish)
    await asyncio.sleep(1)


# TEST FUNCTION

def test(duration):
    global led

    loop = asyncio.get_event_loop()
    duration = int(duration)
    if duration > 0:
        print("Flash LED's for {:3d} seconds".format(duration))
    t = int((0.2 + 1 / 2) * 1000)
    loop.create_task(toggle(led, t))
    loop.create_task(check_connection(300))
    loop.create_task(check_mqtt())
    loop.create_task(make_publish())
    loop.run_forever()
#    loop.run_until_complete(killer(duration))
#    loop.close()


load_config(CONFIG)
setup()
config_mqtt_client()
test(10)
