
#board DOIT devkit ESP32

import ubinascii
import machine, _thread
from machine import Pin

import uasyncio as asyncio
import gc

from relay_control import RelayControl
from button_control import ButtonControl

from wifi import WifiManager
from ftpse import FTPClient

_debug = True
client_id = b"esp32_" + ubinascii.hexlify(machine.unique_id())

import logging
logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger("Runner")

class Runner():

    def __init__(self):
        self.client_id = b"esp32_" + ubinascii.hexlify(machine.unique_id())

        self.wifi = WifiManager()
        self.led2_setup()
        self.b4_setup()

        loop = asyncio.get_event_loop()
        loop.create_task(self._heartbeat())


        loop.create_task(self.wifi.sta_start())

        self.normal = "start"

        self.service = {}

    def _config(self):
        self.relay_setup()


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
                await asyncio.sleep_ms(2000)



    def relay_setup(self):
        sw_1_pin = Pin(26, Pin.OUT)
        sw_1_on = 0
        self.sw_1 = RelayControl(name="sw1", _pin=sw_1_pin, on_value=sw_1_on, default=1-sw_1_on)
        self.sw_1.set_callback(self.relay_cb)

        sw_2_pin = Pin(27, Pin.OUT)
        sw_2_on = 0
        self.sw_2 = RelayControl(name="sw2", _pin=sw_2_pin, on_value=sw_2_on, default=1-sw_2_on)
        self.sw_2.set_callback(self.relay_cb)

    #RELAY CALLBACK
    def relay_cb(self,relay):

        print("SW: %s = %s" % (relay.name, relay.state))


    async def _run_main_loop(self):
        # Loop forever
        mins = 0
        while True:
            gc.collect()  # For RAM stats.
            mem_free = gc.mem_free()
            mem_alloc = gc.mem_alloc()

            print("STA status: %s" % self.wifi.status)
            print("AP status: %s" % self.wifi.status_ap)

            print("Uptime: %s" % mins)
            print("MemFree: %s" % mem_free)
            print("MemAlloc: %s" % mem_alloc)

            print("Services: {}".format(self.service))

            mins += 1

            await asyncio.sleep(60)



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


            if self.service["wifi_AP"]:

                if not self.service["ftp_AP"]:
                        self.service["ftp_AP"] = self.ftpd.run(self.service["wifi_AP"])



            await asyncio.sleep(10)


    async def main(self):

        self.service["wifi_STA"] = False
        self.service["wifi_AP"] = False

        self.service["ftp_STA"] = False
        self.service["ftp_AP"] = False
        self.ftpd = FTPClient(port=25)

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
