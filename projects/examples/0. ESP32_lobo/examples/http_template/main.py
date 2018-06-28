
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
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.connect("WIFI", "PASSWORD")
        utime.sleep_ms(5000)
        print(sta.ifconfig())
        ftp = network.ftp.start(user="micro", password="python", buffsize=1024, timeout=300)
        print("FTP run is:%s" % ftp)



    return r1

if __name__ == '__main__':
    r1 = main()
