import machine
from machine import Timer
from machine import Pin


import time
import ubinascii

import machine
import ubinascii
import sys
import gc
import os
import esp
import network



import sehttp

tim3 = Timer(-1)
debug = True

led2 = machine.Pin(2, machine.Pin.OUT)

def make_publish():

    while True:
        c_sehttp.server_process()
        yield None

publish = make_publish()


def pubm():
    try:
        next(publish)
        return True
    except StopIteration:
        pass

    if debug:
        print("StopIteration")

    machine.reset()



run_period = 100

def run_timer():
    tim3.init(period=run_period, mode=Timer.PERIODIC, callback=lambda t: pubm())


def led_control(_resPath, _queryParams):

    # DEBUG curl -i 'http://192.168.10.112/led?set=&state='
    if debug:
        print("_queryParams =", _queryParams)

    if 'set' in _queryParams:

        set = _queryParams["set"]
        if set == "1" or set == "0":
            set = int(_queryParams["set"])
            led2.value(set)
        else:
            led2.value(1) if led2.value() == 0 else led2.value(0)

    if 'state' in _queryParams:
        return {'state': led2.value()}



def slider_control(_resPath, _queryParams):
    print(_resPath)
    print(_queryParams)

def api_control(_resPath, _queryParams):

    #api?foo=1 , curl -i 'http://192.168.10.111/api?foo=1'
    if 'foo' in _queryParams:
        if _queryParams["foo"] == "1":
            return {'foo': 'bar'}

def system_info(_resPath, _queryParams):
    respone = {}

    # curl -i 'http://192.168.10.111/system?memory='
    if 'memory' in _queryParams:
        mem_alloc = gc.mem_alloc()
        mem_free = gc.mem_free()
        respone['memory'] = {
                'mem_alloc': mem_alloc,
                'mem_free': mem_free
        }

    print respone
    return respone

_routeHandlers = [
	( "/led", "GET", led_control ),
	( "/slider", "GET", slider_control ),
    ( "/api", "GET", api_control ),
    ( "/system", "GET", system_info ),

]


c_sehttp = sehttp.SimpleHttp(port=80, web_path="/www", debug=True, route_handlers=_routeHandlers  )
c_sehttp.start()


def main():

    run_timer()

if __name__ == '__main__':
    main()