from mqttse import MQTTClient
import uasyncio as asyncio
import utime

def clear_messages(key):

    global MESSAGES
    MESSAGES[key] = None


def sub_cb(topic, msg):
    global debug
    print("INF: In sub_cb", topic.decode(), msg.decode())

    if debug:
        print(topic, msg)


def config_mqtt_client():
    global c_mqtt

    try:
        subscribe_topic = CONFIG['topic'] + '/#'
        c_mqtt = MQTTClient(CONFIG['client_id'], CONFIG['broker'],
                            CONFIG['port'], timeout=1,
                            sbt=subscribe_topic, debug=True)
        c_mqtt.set_callback(sub_cb)

        if debug:
            print("attempt connect to MQTT", str(c_mqtt.status))
    except (OSError, ValueError):
        print("Couldn't connect to MQTT")


def check_mqtt(event):
    global c_mqtt
    while True:
        if event.is_set():
            if c_mqtt and c_mqtt.status == 0:
                print("Status_0: Mqtt connection status is: {} and event {}"
                      .format(c_mqtt.status, event.is_set()))
                c_mqtt.communicate()
            if c_mqtt and c_mqtt.status == 1:
                global MESSAGES
                board_uptime = utime.localtime()[4], ":", utime.localtime()[5]
                MESSAGES[CONFIG['topic'] + '/ping'] = '1'
                MESSAGES[CONFIG['topic'] + '/uptime'] = board_uptime
                print("Status_1: Mqtt connection status is: {} and event {}"
                      .format(c_mqtt.status, event.is_set()))
        await asyncio.sleep(15)


async def make_publish(event):
    print("INF: Start Publish and Event is", event.is_set())
    if event.is_set():
        to_mqtt = MESSAGES
        for key, value in to_mqtt.items():
            if value is not None:
                if c_mqtt and c_mqtt.status == 1:
                    retain = False
                    result = c_mqtt.publish(
                        bytes(key, 'utf-8'),
                        bytes(str(value), 'utf-8'),
                        retain, 0)
                    if result == 1:
                        clear_messages(key)
                    if debug:
                        print("Result pub to MQTT", result)
                    c_mqtt.wait_msg()
        await asyncio.sleep(0)


async def wait_msg():
    while True:
        if c_mqtt and c_mqtt.status == 1:
            c_mqtt.wait_msg()
        await asyncio.sleep_ms(500)


async def subscribe():
    while True:
        c_mqtt.communicate()
        subscribe_topic = CONFIG['topic'] + '/#'
        if c_mqtt and c_mqtt.status == 1:
            print("INF: inside wait_msg", CONFIG['topic'])
            c_mqtt.subscribe(subscribe_topic)
        await asyncio.sleep_ms(500)
