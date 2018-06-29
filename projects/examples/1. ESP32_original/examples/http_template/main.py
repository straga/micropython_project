
#board DOIT devkit ESP32


import utime
from runner import Runner


_debug = True
_message = "Run in DEBUG . B4 Control Pin"

def main():

    print("Main = %s" % _message)

    r1 = Runner(debug=_debug)

    print("Wait: Press Control Button")
    utime.sleep_ms(5000)

    if r1.btn_ctrl.state != "ON":
        print("Start Main")
        r1.config()

    else:
        print("Control Button: Activate")

        import network
        import ftp
        import _thread
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.connect("WIFI", "PASSWORD")
        utime.sleep_ms(5000)
        print(sta.ifconfig())
        ftp = _thread.start_new_thread(ftp.ftpserver, ())

        import telnet
        telnet = _thread.start_new_thread(telnet.start, ())


    return r1

if __name__ == '__main__':
    r1 = main()
