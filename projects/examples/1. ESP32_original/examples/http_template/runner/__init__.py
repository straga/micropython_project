

import machine, _thread
from machine import Pin
from relay_control import RelayControl
from button_control import ButtonControl

from httpse import SimpleHttp
from httpse.runner32 import ProcessRuner
from httpse.route_system import SystemHandler
from httpse.route_led import LedHandler
import machine, network, utime

from mqttse import MQTTClient
import ubinascii
import utime


class Runner:
    '''

    '''

    # init
    def __init__(self, debug=False):

        self.debug = debug
        self.wlan = False
        self.mqtt_bus = {}
        self.btn_ctrl = False
        self.button_control()


    def config(self):

        print("Start Config")

        self.wifi()

        self.led2_setup()
        self.btn_ctrl.set_callback(self.btn_ctrl_cb)


        self.client_id = b"esp32_" + ubinascii.hexlify(machine.unique_id())
        # #iot.eclipse.org
        # #192.168.100.240
        #
        self.config = {
            "broker": 'iot.eclipse.org',
            "port": 1883,
            "delay_between_message": -500,
            "client_id": self.client_id,
            "topic": b"devices/" + self.client_id + "/#",
            "ping": b"devices/" + self.client_id + "/ping",
        }

        if self.wlan_check():
            self.http()
            self.start_mqtt()


    #BUTTON CALLBACK

    def btn_ctrl_cb(self):

        if self.btn_ctrl.state == "ON":
            self.led_2.change_state()

        if self.debug:
            print("Button is = %s" % self.btn_ctrl.state)


    def led2_setup(self):

        LED_2_pin = Pin(2, Pin.OUT)
        LED_2_on = 1

        self.led_2 = RelayControl(name="Led2", _pin=LED_2_pin, on_value=LED_2_on, default=LED_2_on)
        self.led_2.set_callback(self.relay_cb)



    #RELAY CALLBACK
    def relay_cb(self,relay):

        if self.debug:
            print("Led: %s = %s" % (relay.name, relay.state))



    #BUTTON CHECK
    def button_push_check(self):

        while True:
            self.btn_ctrl.push_check
            utime.sleep_ms(200)

    def button_control(self, pin=4):

        ctrl_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.btn_ctrl = ButtonControl(name="B4", _pin=ctrl_pin, debug=self.debug, on_value=0, off_value=1)
        self.btn_ctrl.start()

        _ = _thread.stack_size(5 * 1024)
        th1 = _thread.start_new_thread(self.button_push_check, ())



    # #wifi
    def wifi(self):

        print("")
        print("Starting WiFi ...")
        sta_if = network.WLAN(network.STA_IF)
        _ = sta_if.active(True)
        sta_if.connect("WIFI", "PASSWORD")
        utime.sleep_ms(10000)

        if sta_if.isconnected():
            ifcfg = sta_if.ifconfig()
            print("WiFi started, IP:", ifcfg[0])
            self.wlan = sta_if
            import ftp
            ftp = _thread.start_new_thread(ftp.ftpserver, ())

            import telnet
            telnet = _thread.start_new_thread(telnet.start, ())

        else:
            print("No connect to WiFi ...")


    def wlan_check(self):

        if self.wlan:
            return self.wlan.isconnected()
        else:
            return False



    #HTTP

    # #http
    def http(self):

        _routeHandlers = []

        # System
        _routeHandlers.append(SystemHandler(debug=self.debug).route_handler)
        _routeHandlers.append(LedHandler(debug=self.debug, relay=self.led_2).route_handler)


        if self.debug:
            print("Routes = %s" % _routeHandlers)

        server_sehttp = SimpleHttp(port=80, web_path="/www", debug=self.debug, route_handlers=_routeHandlers)
        server_sehttp.start()

        if server_sehttp.started:
            server_sehttp_runner = ProcessRuner(http_server=server_sehttp, debug=self.debug)
            server_sehttp_runner.start_http()


    # #mqtt
    def mqtt_sub_cb(self, topic, msg):

        self.c_mqtt.status == 0

        if topic == self.config['ping']:

            if msg.decode() == "1":
                self.c_mqtt.status == 1


        if self.debug:
            print("Sub Message: Pub: %s, %s" % (topic.decode(), msg.decode()))


    def mqtt(self):
        self.c_mqtt = False
        try:
            self.c_mqtt = MQTTClient(self.config['client_id'],
                                     self.config['broker'],
                                     self.config['port'],
                                     timeout=1,
                                     sbt=self.config['topic'],
                                     debug=True)

            self.c_mqtt.set_callback(self.mqtt_sub_cb)

        except (OSError, ValueError):
            print("Couldn't connect to MQTT")



    def mqtt_check(self):

        delay_send_message = -300
        delay_wait_message = -1000

        while True:
            if self.wlan_check():

                if self.c_mqtt and self.c_mqtt.status == 0:
                    self.c_mqtt.communicate()

                if self.c_mqtt and self.c_mqtt.status == 1:

                    retain = False

                    if self.mqtt_bus:

                        for key, value in  self.mqtt_bus.items():
                            t_start = utime.ticks_ms()

                            if value:
                                # DEBUG
                                if self.debug:
                                    print("Message Ready: Pub: %s, %s" % (key, value))

                                result = self.c_mqtt.publish(self.config[key], bytes(value, 'utf-8'), retain)

                                while utime.ticks_diff(t_start, utime.ticks_ms()) >= delay_send_message:
                                    yield None

                                if result == 1:
                                    self.mqtt_bus[key] = None

                                # DEBUG
                                if self.debug:
                                    print("Result pub to MQTT", result)

                    #wait_message
                    w_t_start = utime.ticks_ms()
                    while utime.ticks_diff(w_t_start, utime.ticks_ms()) >= delay_wait_message:
                        yield None

                    print("Before wait_msg")
                    self.c_mqtt.wait_msg()
                    self.mqtt_bus['ping'] = '1'
            # else:
            #     if self.debug:
            #         print("Error: No Wifi connect")

            yield True







    def _run_mqtt_process(self):


        pubwait = self.mqtt_check()

        while True:
            try:
                next(pubwait)
            except StopIteration:
                if self.debug:
                    print("StopIteration")

            utime.sleep_ms(1000)

    def start_mqtt(self):

        self.mqtt()

        _thread.stack_size(4 * 1024)
        self._http_thread = _thread.start_new_thread(self._run_mqtt_process, ())


    #
    #
    #
    # #mqtt
    # def mqtt_sub_cb(self, topic, msg):
    #
    #     self.c_mqtt.status == 0
    #
    #     if topic == self.config['ping']:
    #
    #         if msg.decode() == "1":
    #             self.c_mqtt.status == 1
    #
    #
    #     if self.debug:
    #         print("Sub Message: Pub: %s, %s" % (topic.decode(), msg.decode()))
    #
    #
    # def mqtt(self):
    #     self.c_mqtt = False
    #     try:
    #         self.c_mqtt = MQTTClient(self.config['client_id'],
    #                                  self.config['broker'],
    #                                  self.config['port'],
    #                                  timeout=1,
    #                                  sbt=self.config['topic'],
    #                                  debug=True)
    #
    #         self.c_mqtt.set_callback(self.mqtt_sub_cb)
    #
    #     except (OSError, ValueError):
    #         print("Couldn't connect to MQTT")
    #
    #
    #
    # def mqtt_check(self):
    #
    #     delay_send_message = -300
    #     delay_wait_message = -1000
    #
    #     while True:
    #         if self.wlan_check():
    #
    #             if self.c_mqtt and self.c_mqtt.status == 0:
    #                 self.c_mqtt.communicate()
    #
    #             if self.c_mqtt and self.c_mqtt.status == 1:
    #
    #                 retain = False
    #
    #                 if self.mqtt_bus:
    #
    #                     for key, value in  self.mqtt_bus.items():
    #                         t_start = utime.ticks_ms()
    #
    #                         if value:
    #                             # DEBUG
    #                             if self.debug:
    #                                 print("Message Ready: Pub: %s, %s" % (key, value))
    #
    #                             result = self.c_mqtt.publish(self.config[key], bytes(value, 'utf-8'), retain)
    #
    #                             while utime.ticks_diff(t_start, utime.ticks_ms()) >= delay_send_message:
    #                                 yield None
    #
    #                             if result == 1:
    #                                 self.mqtt_bus[key] = None
    #
    #                             # DEBUG
    #                             if self.debug:
    #                                 print("Result pub to MQTT", result)
    #
    #                 #wait_message
    #                 w_t_start = utime.ticks_ms()
    #                 while utime.ticks_diff(w_t_start, utime.ticks_ms()) >= delay_wait_message:
    #                     yield None
    #
    #                 print("Before wait_msg")
    #                 self.c_mqtt.wait_msg()
    #                 self.mqtt_bus['ping'] = '1'
    #         # else:
    #         #     if self.debug:
    #         #         print("Error: No Wifi connect")
    #
    #         yield True
    #
    #
    #
    #
    #
    #
    #
    # def _run_mqtt_process(self):
    #
    #
    #     pubwait = self.mqtt_check()
    #
    #     while True:
    #         try:
    #             next(pubwait)
    #         except StopIteration:
    #             if self.debug:
    #                 print("StopIteration")
    #
    #         _thread.wait(1000)
    #
    # def start_mqtt(self):
    #
    #     self.mqtt()
    #
    #     _thread.stack_size(4 * 1024)
    #     self._http_thread = _thread.start_new_thread("MqttSe", self._run_mqtt_process, ())
    #
    #
    #
    # #http
    # def http(self):
    #
    #     _routeHandlers = []
    #
    #     # System
    #     _routeHandlers.append(SystemHandler(debug=self.debug).route_handler)
    #     _routeHandlers.append(LedHandler(debug=self.debug, relay=self.led_2).route_handler)
    #
    #
    #     if self.debug:
    #         print("Routes = %s" % _routeHandlers)
    #
    #     server_sehttp = SimpleHttp(port=80, web_path="/flash/www", debug=self.debug, route_handlers=_routeHandlers)
    #     server_sehttp.start()
    #
    #     if server_sehttp.started:
    #         server_sehttp_runner = ProcessRuner(http_server=server_sehttp, debug=self.debug)
    #         server_sehttp_runner.start_http()
    #
    #
    # #wifi
    # def wifi(self):
    #
    #     print("")
    #     print("Starting WiFi ...")
    #     sta_if = network.WLAN(network.STA_IF)
    #     _ = sta_if.active(True)
    #     sta_if.connect("dd-wrt", "poromona")
    #     utime.sleep_ms(10000)
    #
    #     if sta_if.isconnected():
    #         ifcfg = sta_if.ifconfig()
    #         print("WiFi started, IP:", ifcfg[0])
    #         self.wlan = sta_if
    #         network.ftp.start(user="micro", password="python", buffsize=1024, timeout=300)
    #
    #     else:
    #         print("No connect to WiFi ...")
    #
    #
    #
    #
    #
    #
    # #BUTTON CALLBACK
    #
    # def b4_cb(self):
    #
    #     if self.btn_ctrl.state == "ON":
    #         self.led_2.change_state()
    #
    #     if self.debug:
    #         print("Button is = %s" % self.btn_ctrl.state)
    #
    #
    # def led2_setup(self):
    #
    #     LED_2_pin = Pin(2, Pin.INOUT)
    #     LED_2_on = 1
    #
    #     self.led_2 = RelayControl(name="Led2", _pin=LED_2_pin, on_value=LED_2_on, default=LED_2_on)
    #     self.led_2.set_callback(self.relay_cb)
    #
    #
    #
    # #RELAY CALLBACK
    # def relay_cb(self,relay):
    #
    #     if self.debug:
    #         print("Led: %s = %s" % (relay.name, relay.state))
