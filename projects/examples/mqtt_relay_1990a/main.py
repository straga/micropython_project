# -*- coding: utf-8 -*-
import machine
from machine import Timer
import time
from simple import MQTTClient
import ubinascii
from machine import Pin, PWM
import ubinascii
import relay_control
import onewire
from button_control import ButtonControl

tim1 = Timer(-1)
tim2 = Timer(-1)
tim3 = Timer(-1)
tim4 = Timer(-1)
tim5 = Timer(-1)
tim6 = Timer(-1)




global debug
debug = False

global tem1
tem1 = False


client_id = b"esp8266_" + ubinascii.hexlify(machine.unique_id())

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
    "DS1990A" : b"devices/" + client_id + "/DS1990A/rom",
}

allowed = ["01eeb611000100a7", "010ccf10000100f1", "014a0c11000100d5", "01f71f11000100aa"]

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

    # the device is on GPIO12
    dat = machine.Pin(4)

    #create the onewire object
    global ds
    ds = onewire.OneWire(dat)

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

                    while time.ticks_diff(t_start, time.ticks_ms()) <= -1000:  # 2000mS delay
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




        # while time.ticks_diff(t_start, time.ticks_ms()) <= 10000:  # 15000mS delay
        #     yield None



        yield True


def sub_cb(topic, msg):
    if topic.decode() == CONFIG['sw1_set']:

        if msg.decode() == "ON":
            relay_1.set_state(relay_on)

        if msg.decode() == "OFF":
            relay_1.set_state(relay_off)


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

        c_mqtt.con2()
        relay_1.set_state(relay_off)

    global MESSAGES
    MESSAGES['ping'] = '1'

def pulse_relay():
    tim6.init(period=5000, mode=Timer.ONE_SHOT, callback=lambda t: relay_1.set_state(relay_off))


def rom_1990A():

    # scan for devices on the bus
    global roms
    global tem1
    MESSAGES['DS1990A'] = None
    tem1 = False
    roms = False
    roms = ds.scan()
    if roms:
        romId = ubinascii.hexlify(roms[0])
        print("Rom Found: {}\n".format(romId))

        if romId:
            MESSAGES['DS1990A'] = romId.decode("utf-8")
            if romId.decode("utf-8") in allowed:
                relay_1.set_state(relay_on)
                pulse_relay()
                
        else:
            MESSAGES['DS1990A'] = None


# RELAY

def relay_cb(relay):

    if relay.save_state != relay.state:
        relay.save_state = relay.state

        MESSAGES[relay.name + "_state"] = relay.state

        if debug:
            print(relay.state)


relay_pin_1 = 5

relay_on = 1
relay_off = 0

relay_1 = relay_control.RELAY(name="sw1",pin_num = relay_pin_1, on_value = relay_on)

relay_1.set_callback(relay_cb)


# BUTTON
button_pin_1 = 14 #D5


def wait_msg():

    if c_mqtt and c_mqtt.status == 1:
        c_mqtt.wait_msg()


def pubm():

    next(publish)


ctrl_pin = Pin(button_pin_1, Pin.IN, Pin.PULL_UP)
b2 = ButtonControl(name="B4", _pin=ctrl_pin, debug=debug, on_value=0, off_value=1)
b2.start()



#BUTTON CALLBACK

def btn_ctrl_cb():

    if b2.state == "ON":
        relay_1.set_state(relay_on)
        pulse_relay()


b2.set_callback(btn_ctrl_cb)


def push():
    b2.push_check

def run_timer():

    tim5.init(period=300, mode=Timer.PERIODIC, callback=lambda t: push())

    tim1.init(period=15000, mode=Timer.PERIODIC, callback=lambda t: check())
    tim2.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: wait_msg())
    tim3.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: pubm())

    #uncomment if DS18B20 present, or freezed every 20sec.
    tim4.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: rom_1990A())


    # tim5.init(period=60000, mode=Timer.PERIODIC, callback=lambda t: get_relay_status(1))
    


def main():

    config_mqtt_client()
    run_timer()


if __name__ == '__main__':
    load_config()
    setup()
    main()
