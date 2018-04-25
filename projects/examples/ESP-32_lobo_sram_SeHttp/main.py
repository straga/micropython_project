import machine
from machine import Timer

from httpse import SimpleHttp
from httpse.runner32 import ProcessRuner
from httpse.route_system import SystemHandler
from httpse.route_led import LedHandler
from relay_control import RELAY
from mqttse import MQTTClient

import ubinascii

client_id = b"esp8266_" + ubinascii.hexlify(machine.unique_id())

CONFIG = {
    "broker": '192.168.2.153',
    "port" : 1883,
    "sensor_pin": 14,
    "delay_between_message" : -500,
    "client_id": client_id,
    "r1_mode": "OFF",
    "r1_tmax": 20.5,
    "r1_tmin": 18,
    "topic": b"devices/"+client_id+"/#",
    "ping" : b"devices/"+client_id+"/ping",
    "sw1_set" : b"devices/"+client_id+"/sw1/set",
    "sw1_state" : b"devices/"+client_id+"/sw1/state",
    "sw2_set": b"devices/" + client_id + "/sw2/set",
    "sw2_state": b"devices/" + client_id + "/sw2/state",
    "DS18B20": b"devices/" + client_id + "/18b20",
    "t_ctr_r1_mode_set": b"devices/" + client_id + "/t_ctr_r1/mode/set",
    "t_ctr_r1_mode_state": b"devices/" + client_id + "/t_ctr_r1/mode/state",
    "t_ctr_r1_max": b"devices/" + client_id + "/t_ctr_r1/max",
    "t_ctr_r1_min": b"devices/" + client_id + "/t_ctr_r1/min",
    "m_delay": b"devices/" + client_id + "/m_delay",

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


try:
    c_mqtt = MQTTClient(CONFIG['client_id'], CONFIG['broker'], CONFIG['port'], timeout=1, sbt=CONFIG['topic'],
                        debug=False)

except (OSError, ValueError):
    print("Couldn't connect to MQTT")


_debug = True
_routeHandlers = []

#System
_routeHandlers.append(SystemHandler(debug=_debug).route_handler)


#Led
LED_2_pin = 5
LED_2 = RELAY(name="Led2", pin_num=LED_2_pin, on_value=0, off_value=1, state_on=1, state_off=0, default=1)
_routeHandlers.append(LedHandler(debug=_debug, relay=LED_2).route_handler)


def main():
    if _debug:
        print("Routes = %s" % _routeHandlers)

    server_sehttp = SimpleHttp(port=80, web_path="/flash/www", debug=_debug, route_handlers=_routeHandlers)
    server_sehttp.start()

    if server_sehttp.started:
        server_sehttp_runner = ProcessRuner(http_server=server_sehttp, debug=_debug)
        server_sehttp_runner.start_http()



def ftp():
    import ftp
    ftp.ftpserver()

if __name__ == '__main__':
    main()

# _routeHandlers = [
# 	( "/led", "GET", led_control ),
# 	( "/slider", "GET", slider_control ),
#     ( "/api", "GET", api_control ),
#     ( "/system", "GET", system_info ),
#
# ]