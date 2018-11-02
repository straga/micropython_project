from mqttse import MQTTClient
import asyn
import uasyncio as asyncio
from config import *
from checkconnection import check_connection
from mqtt_helpers import *
from basesensor import BaseSensor
import builtins

# Board specific modules
from si7021sensor import SI7021sensor


builtins.MESSAGES = {}
builtins.debug = True
builtins.CONFIG = {}
builtins.loop = asyncio.get_event_loop()
builtins.event = asyn.Event()
list_of_instances = []


if init_config():
    load_config(CONFIG)
else:
    save_default_config()


class Sensor01(BaseSensor, SI7021sensor):
    publish_state_to_mqtt = True

    def __init__(self):
        super(Sensor01, self).__init__()
        print('Sensor class 01')
        list_of_instances.append(self)


i_Sensor = Sensor01()

config_mqtt_client()
check_mqtt(event)
check_connection(event)


async def check_hw_state():
    while True:
        for instance in list_of_instances:
            instance.action_on_change("hw", instance.get_state())
        await asyncio.sleep_ms(5000)




loop.create_task(check_mqtt(event))
#loop.create_task(make_publish(event))
loop.create_task(wait_msg())
loop.create_task(check_hw_state())
loop.create_task(check_connection(event))
loop.run_forever()
