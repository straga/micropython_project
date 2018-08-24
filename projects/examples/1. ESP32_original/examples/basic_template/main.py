
#board DOIT devkit ESP32

import ubinascii
import machine, _thread
from machine import Pin, I2C

import uasyncio as asyncio
import gc

from relay_control import RelayControl
from button_control import ButtonControl

from wifi import WifiManager
from ftpse import FTPClient
from telnetse import TelnetServer

import json

_debug = True
client_id = b"esp32_" + ubinascii.hexlify(machine.unique_id())
client_id = client_id.decode()

import logging
logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger("Runner")

class Runner():

    def __init__(self):

        loop = asyncio.get_event_loop()
        self.normal = "start"
        self.service = {}

        #FTP
        self.ftpd = FTPClient(port=25)

        #telnet
        self.telnet = TelnetServer()

        #button control
        self.b4_setup()

        #LED - Heartbeat
        self.led2_setup()
        loop.create_task(self._heartbeat())

        #WIFI
        self.wifi = WifiManager()
        loop.create_task(self.wifi.sta_start())


        #services
        self.service["wifi_STA"] = False
        self.service["wifi_AP"] = False

        self.service["ftp_STA"] = False
        self.service["ftp_AP"] = False

        self.service["telnet"] = False

        self.service["mqtt"] = False
        self.mqtt = False

        self.service["http"] = False







    def _config(self):
        #Relay

        self.relay_setup()

        #MQTT
        from mqttse import MQTTClient

        self.mqtt = MQTTClient(client_id)

        # "local1": "192.168.100.240",
        # "local2": "192.168.254.1",
        # "eclipse": "iot.eclipse.org"

        self.mqtt.server = "192.168.100.240"

        self.mqtt.set_callback(self.mqtt_sub_cb)

        self.mqtt.set_topic("status", "status")
        self.mqtt.set_topic("services", "services")

        self.mqtt.set_topic("sw1_set", "sw1/set")
        self.mqtt.set_topic("sw1_state", "sw1/state")

        self.mqtt.set_topic("sw2_set", "sw2/set")
        self.mqtt.set_topic("sw2_state", "sw2/state")

        #i2c
        # esp32i2cPins = {'sda': 23, 'scl': 22}
        # sclPin = esp32i2cPins['scl']
        # sdaPin = esp32i2cPins['sda']
        i2c = I2C(scl=Pin(22), sda=Pin(23))

        #si7021
        from si7021 import SI7021
        self.s_si = SI7021(i2c)
        self.s_si.read_delay = 30
        self.s_si.sensor_detect()
        self.s_si.start()

        self.mqtt.set_topic("si_t", "si/temperature")
        self.mqtt.set_topic("si_h", "si/humidity")

        self.s_si.set_callback(self.s_si_cb)


        #bmp180
        from bmp180 import BMP180
        self.s_bmp = BMP180(i2c)
        self.s_bmp.read_delay = 30
        self.s_bmp.sensor_detect()
        self.s_bmp.start()

        self.mqtt.set_topic("bmp_t", "bmp/temperature")
        self.mqtt.set_topic("bmp_h", "bmp/pressure")
        self.mqtt.set_topic("bmp_a", "bmp/altitude")

        self.s_bmp.set_callback(self.s_bmp_cb)


        #http

        from httpse import HTTPSE
        from httpse.route_system import SystemHandler
        from httpse.route_led import LedHandler

        _routeHandlers = []
        _routeHandlers.append(SystemHandler().route_handler)
        _routeHandlers.append(LedHandler(relay=self.sw_1).route_handler)

        self.http = HTTPSE(route_handlers=_routeHandlers)




    def s_bmp_cb(self):

        if self.mqtt:
            self.mqtt.mqtt_bus["bmp_t"] = self.s_bmp.temperature
            self.mqtt.mqtt_bus["bmp_h"] = self.s_bmp.pressure
            self.mqtt.mqtt_bus["bmp_a"] = self.s_bmp.altitude

    def s_si_cb(self):

        if self.mqtt:
            self.mqtt.mqtt_bus["si_t"] = self.s_si.temperature
            self.mqtt.mqtt_bus["si_h"] = self.s_si.humidity




    #MQTT
    def mqtt_sub_cb(self, topic, msg):

        # print("Sub Message: Pub: %s, %s" % (topic.decode(), msg.decode()))
        # print("TOPIC sw1_set , %s" % (self.mqtt.topics['sw1_set']))

        if topic.decode() == self.mqtt.topics['sw1_set']:
            # print("1")

            if msg.decode() == "ON":
                # print("on")
                self.sw_1.on()

            if msg.decode() == "OFF":
                # print("off")
                self.sw_1.off()

        if topic.decode() == self.mqtt.topics['sw2_set']:

            if msg.decode() == "ON":
                self.sw_2.on()
            if msg.decode() == "OFF":
                self.sw_2.off()


    # BUTTON b4
    def b4_setup(self):
        pin = 4
        ctrl_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.btn_ctrl = ButtonControl(name="B4", _pin=ctrl_pin, debug=True, on_value=0, off_value=1)
        self.btn_ctrl.set_callback(self.b4_cb)


    def b4_cb(self):

        if self.btn_ctrl.state == "ON":
            if self.normal == "start":
                self.normal = "fail"
                print("Start Fail Safe Mode")

            print("Button is = %s" % self.btn_ctrl.state)

        if self.btn_ctrl.state == "OFF":
            print("Button is = %s" % self.btn_ctrl.state)



    # Blink flash LED
    def led2_setup(self):
        LED_2_pin = Pin(2, Pin.OUT)
        LED_2_on = 1
        self.led_2 = RelayControl(name="Led2", _pin=LED_2_pin, on_value=LED_2_on, default=LED_2_on)

    async def _heartbeat(self):
        while True:

            if not self.wifi.status and not self.wifi.status_ap:
                self.led_2.on()
                await asyncio.sleep_ms(100)
                self.led_2.off()
                await asyncio.sleep_ms(200)

            if self.wifi.status:
                self.led_2.off()
                await asyncio.sleep_ms(500)
                self.led_2.on()
                await asyncio.sleep_ms(5000)

            if self.wifi.status_ap:
                self.led_2.off()
                await asyncio.sleep_ms(200)
                self.led_2.on()
                await asyncio.sleep_ms(1000)



    # RELAY
    def relay_setup(self):
        sw_1_pin = Pin(26, Pin.OUT)
        sw_1_on = 0
        self.sw_1 = RelayControl(name="sw1", _pin=sw_1_pin, on_value=sw_1_on, default=1-sw_1_on)
        self.sw_1.set_callback(self.relay_cb)

        sw_2_pin = Pin(27, Pin.OUT)
        sw_2_on = 0
        self.sw_2 = RelayControl(name="sw2", _pin=sw_2_pin, on_value=sw_2_on, default=1-sw_2_on)
        self.sw_2.set_callback(self.relay_cb)


    def relay_cb(self,relay):

        if self.mqtt:
            self.mqtt.mqtt_bus[relay.name + '_state'] = relay.get_state()

        print("SW: %s = %s" % (relay.name, relay.state))


    #Main Loop
    async def _run_main_loop(self):
        # Loop forever
        mins = 0
        while True:
            gc.collect()  # For RAM stats.
            mem_free = gc.mem_free()
            mem_alloc = gc.mem_alloc()

            print("STA status: {}".format(self.wifi.status))
            print("AP status: {}".format(self.wifi.status_ap))

            self.status = {
                "Uptime": "{}".format(mins),
                "MemFree": "{}".format(mem_free),
                "MemAlloc": "{}".format(mem_alloc)
            }

            print("Status: {}".format(self.status))
            print("Services: {}".format(self.service))
            # print("Uptime: {}".format(mins))
            # print("MemFree: {}".format(mem_free))
            # print("MemAlloc: {}".format(mem_alloc))
            # print("Services: {}".format(self.service))

            if self.mqtt:
                self.mqtt.mqtt_bus["status"] = ("{}".format(self.status))
                self.mqtt.mqtt_bus["services"] = ("{}".format(self.service))

            mins += 1

            await asyncio.sleep(60)


    #Service Loop
    async def _run_service_loop(self):

        while True:

            if self.wifi.status:
                self.service["wifi_STA"] = self.wifi.wlan().ifconfig()[0]

            else:
                self.service["wifi_STA"] = False

            if self.wifi.status_ap:
                self.service["wifi_AP"] = self.wifi.accesspoint().ifconfig()[0]
            else:
                self.service["wifi_AP"] = False


            if self.service["wifi_STA"]:

                if not self.service["ftp_STA"]:
                        self.service["ftp_STA"] = self.ftpd.run(self.service["wifi_STA"])

                if not self.service["mqtt"] and self.mqtt:
                    self.service["mqtt"] = self.mqtt.run()

                if not self.service["telnet"]:
                    self.service["telnet"] = self.telnet.start()

                if not self.service["http"] and self.http:
                    self.service["http"] = self.http.start()


            if self.service["wifi_AP"]:

                if not self.service["ftp_AP"]:
                        self.service["ftp_AP"] = self.ftpd.run(self.service["wifi_AP"])

                if not self.service["telnet"]:
                    self.service["telnet"] = self.telnet.start()

                if not self.service["http"] and self.http:
                    self.service["http"] = self.http.start()





            await asyncio.sleep(10)


    async def main(self):

        print("Wait: Press Control Button")
        await asyncio.sleep(10)



        if self.normal is not "fail":
            print("Start: Normal Mode")
            self._config()
            self.normal = "run"

        log.info("Start Service Loop")
        loop = asyncio.get_event_loop()
        loop.create_task(self._run_service_loop())

        log.info("Start main_loop")
        while True:
            try:
                await self._run_main_loop()
            except Exception as e:
                print("Global communication failure: %s " % e)



def main():

    print("Run on: %s , B4 pin Control" % client_id)

    global runner
    runner = Runner()

    loop = asyncio.get_event_loop()
    loop.create_task(runner.main())

    _ = _thread.stack_size(7 * 1024)
    _thread.start_new_thread(loop.run_forever, ())


if __name__ == '__main__':

    print("MAIN")
    main()
