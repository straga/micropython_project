import network
import utime
import gc
import uasyncio as asyncio

net_fail_count = 0
net_succ_count = 0


async def check_connection(event):
    global net_fail_count
    global net_succ_count
    while True:
        sta_if = network.WLAN(network.STA_IF)
        is_connected = sta_if.isconnected()
        if not is_connected:
            net_succ_count = 0
            net_fail_count += 1
            if net_fail_count >= 10:
                from machine import reset
                reset()
        else:
            event.set()
            net_succ_count += 1
            if net_succ_count >= 5:
                net_fail_count = 0
        if debug:
            print ("Time is:", utime.localtime()[4], ":", utime.localtime()[5],
                   "WIFI is connected: ", event.is_set(),
                   "Nr times failed: ", net_fail_count, net_succ_count,
                   "Free memory: ", gc.mem_free())
        await asyncio.sleep(10)
