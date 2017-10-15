import machine
from machine import Timer
from machine import Pin
import button_control
import relay_control

import time
import ubinascii

from mqtt_simple import MQTTClient

client_id = b"esp8266_D_" + ubinascii.hexlify(machine.unique_id())


#CONFIG
CONFIG = {
    "broker": '192.168.2.153',
    "port" : 1883,
    "sensor_pin": 14,
    "delay_between_message" : -500,
    "client_id": client_id,
    "topic": b"devices/"+client_id+"/#",
    "ping" : b"devices/"+client_id+"/ping",
    "sw1_set" : b"devices/"+client_id+"/sw1/set",
    "sw1_state" : b"devices/"+client_id+"/sw1/state",
    "sw2_set": b"devices/" + client_id + "/sw2/set",
    "sw2_state": b"devices/" + client_id + "/sw2/state",
    "DS18B20": b"devices/" + client_id + "/18b20",
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


def get_value_human(value):

    if value == "OFF":
        return 0
    if value == "ON":
        return 1
    return None

def set_value_human(value):

    if value == 1:
        return "OFF"
    if value == 0:
        return "ON"
    return None


#MESSAGE
MESSAGES = {
        # 'wait_msg' : '1'
    }

def get_messages():
    return MESSAGES

def clear_messages(key):
    MESSAGES[key] = None

#MAIN
debug = True

#RELAY

def relay_cb(relay):

    if relay.save_state != relay.state:
        relay.save_state = relay.state

        MESSAGES[relay.name+"_state"] = relay.state

        if debug:
            print(relay.state)


relay_pin_1 = 12
relay_pin_2 = 13

relay_on = 1
relay_off = 0

relay_1 = relay_control.RELAY(name="sw1" ,pin_num = relay_pin_1,on_value = relay_on)
relay_2 = relay_control.RELAY(name="sw2" ,pin_num = relay_pin_2,on_value = relay_on)

relay_1.set_callback(relay_cb)
relay_2.set_callback(relay_cb)



#BUTTON
button_pin_1 = 0
button_pin_2 = 2

b2 = button_control.PinButton(button_pin_1, Pin.PULL_UP, debug=True, relay_control=relay_1 )
b0 = button_control.PinButton(button_pin_2, Pin.PULL_UP, debug=True, relay_control=relay_2 )

b0.start()
b2.start()

#SENSORS

# create the onewire object
import onewire, ds18x20
dat = machine.Pin(CONFIG["sensor_pin"])
ds = ds18x20.DS18X20(onewire.OneWire(dat))
roms = False
tem1 = False

def get_18b20():

    MESSAGES['DS18B20'] = None
    tem1 = False
    roms = ds.scan()
    if roms:
        ds.convert_temp()
        temp = ds.read_temp(roms[0])

        if temp:
            MESSAGES['DS18B20'] = str(temp)
            tem1 = float(temp)
        else:
            tem1 = False
            MESSAGES['DS18B20'] = None


#TIMER
tim1 = Timer(-1)
tim2 = Timer(-1)
tim3 = Timer(-1)
tim4 = Timer(-1)
tim5 = Timer(-1)


#MQTT

c_mqtt = None

# delay_between_message = CONFIG['delay_between_message']
delay_between_message = -200 #500 ms

def sub_cb(topic, msg):

    if topic == CONFIG['sw2_set']:

        if msg.decode() == "ON":
            relay_2.set_state(relay_on)

        if msg.decode() == "OFF":
            relay_2.set_state(relay_off)

    if topic == CONFIG['sw1_set']:

        if msg.decode() == "ON":
            relay_1.set_state(relay_on)

        if msg.decode() == "OFF":
            relay_1.set_state(relay_off)

    if debug:
        print(topic.decode(), msg.decode())



try:
    c_mqtt = MQTTClient(CONFIG['client_id'], CONFIG['broker'], CONFIG['port'], timeout=1, sbt=CONFIG['topic'],
                        debug=False)

    c_mqtt.set_callback(sub_cb)

except (OSError, ValueError):
    print("Couldn't connect to MQTT")


def check():

    if c_mqtt and c_mqtt.status == 0:
        c_mqtt.con2()


    global MESSAGES
    MESSAGES['ping'] = '1'


def make_publish():


    while True:

        to_mqtt = get_messages()

        # HARD DEBUG
        # if debug:
        #     print("Message to MQTT", to_mqtt)

        if to_mqtt:

            for key, value in to_mqtt.items():
                t_start = time.ticks_ms()

                if value:
                    #DEBUG
                    if debug:
                        print("Message Ready: Pub: %s, %s" % (key, value))

                    if c_mqtt and c_mqtt.status == 1:
                        retain = False

                        if key == 'sw2_state' or  key == 'sw1_state':
                            retain = True

                        result = c_mqtt.publish(CONFIG[key], bytes(value, 'utf-8'), retain)

                        while time.ticks_diff(t_start, time.ticks_ms()) >= delay_between_message:  #check message send result
                            yield None

                        if result == 1:
                            clear_messages(key)

                        # DEBUG
                        if debug:
                            print("Result pub to MQTT", result)

        yield True

def wait_msg():

    if c_mqtt and c_mqtt.status == 1:
        c_mqtt.wait_msg()


publish = make_publish()
def pubm():
    try:
        next(publish)
    except StopIteration:

        if debug:
            print("StopIteration")





#BUTTON CHECK
def push():

    b0.push
    b2.push

def run_timer():

    tim5.init(period=300, mode=Timer.PERIODIC, callback=lambda t: push())

    tim1.init(period=15000, mode=Timer.PERIODIC, callback=lambda t: check())
    tim2.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: wait_msg())
    tim3.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: pubm())

    #uncomment if DS18B20 present, or freezed every 20sec.
    tim4.init(period=20000, mode=Timer.PERIODIC, callback=lambda t: get_18b20())

def main():
    run_timer()

if __name__ == '__main__':
    main()