import usocket as socket
import ustruct as struct

class MQTTClient:

    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0,
                 ssl=False, ssl_params={}, timeout=1, sbt=None, debug=False):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = client_id
        self.sock = None
        self.server = server
        self.port = port
        self.ssl = ssl
        self.ssl_params = ssl_params
        self.pid = 0
        self.cb = None
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.timeout = timeout
        self.sbt = sbt
        self.status = 0
        self.debug = debug


    def con2(self):
        if self.sock:
            self.sock.close()
        self.sock_connect()
        self.connect(clean_session=True)
        if self.sbt:
            self.subscribe(self.sbt)
        self.status = 1


    def write(self, write_data, arg=None):

        if not self.sock:
            self.sock_connect()

        try:
            self.sock.settimeout(self.timeout)
            if arg:
                self.sock.write(write_data, arg)
            else:
                self.sock.write(write_data)
        except OSError as e:
            self.status = 0
            return None
        self.status = 1


    def _send_str(self, s):
        self.write(struct.pack("!H", len(s)))
        self.write(s)


    def _recv_len(self):
        n = 0
        sh = 0

        b = self.sock.read(1)[0]
        n |= (b & 0x7f) << sh
        if not b & 0x80:
            return n
        sh += 7


    def set_callback(self, f):
        self.cb = f

    def sock_connect(self):
        self.sock = socket.socket()
        self.sock.settimeout(self.timeout)

    def connect(self, clean_session=True):

        addr = socket.getaddrinfo(self.server, self.port)[0][-1]

        if not self.sock:
            self.sock_connect()

        try:
            self.sock.connect(addr)
        except OSError as e:
            return None

        if self.ssl:
            import ussl
            self.sock = ussl.wrap_socket(self.sock, **self.ssl_params)
        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\x02\0\0")

        sz = 10 + 2 + len(self.client_id)
        msg[6] = clean_session << 1
        if self.user is not None:
            sz += 2 + len(self.user) + 2 + len(self.pswd)
            msg[6] |= 0xC0
        if self.keepalive:
            assert self.keepalive < 65536
            msg[7] |= self.keepalive >> 8
            msg[8] |= self.keepalive & 0x00FF

        i = 1
        while sz > 0x7f:
            premsg[i] = (sz & 0x7f) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz

        self.sock.write(premsg, i + 2)
        self.write(msg)

        self._send_str(self.client_id)

        if self.user is not None:
            self._send_str(self.user)
            self._send_str(self.pswd)

        try:
            self.sock.read(4)
        except OSError as e:
            return None

    def disconnect(self):

        try:
            self.sock.write(b"\xe0\0")
        except OSError as e:
            print(e)
        self.sock.close()

    def publish(self, topic, msg, retain=False, qos=0):

        pkt = bytearray(b"\x30\0\0\0")
        pkt[0] |= qos << 1 | retain
        sz = 2 + len(topic) + len(msg)
        if qos > 0:
            sz += 2
        if sz > 2097152:
            return None
        i = 1
        while sz > 0x7f:
            pkt[i] = (sz & 0x7f) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz

        self.write(pkt, i + 1)
        self._send_str(topic)
        self.write(msg)

        return 1

    def subscribe(self, topic, qos=0):

        if self.cb:
            pkt = bytearray(b"\x82\0\0\0")
            self.pid += 1
            struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
            self.write(pkt)
            self._send_str(topic)
            self.write(qos.to_bytes(1, "little"))

            op = self.wait_msg()
            if op == 0x90:
                try:
                    resp = self.sock.read(4)
                except OSError as e:
                    return None
                return None
        else:
            print("Subscribe callback is not set")
            return None

    def wait_msg(self):

        try:
            self.sock.settimeout(0)
            res = self.sock.read(1)
        except OSError as e:
            return None

        if res is None or res == b"":
            return None

        op = res[0]
        if op & 0xf0 != 0x30:
            return op
        sz = self._recv_len()
        topic_len = self.sock.read(2)
        topic_len = (topic_len[0] << 8) | topic_len[1]
        topic = self.sock.read(topic_len)
        sz -= topic_len + 2
        pid = self.pid
        if op & 6:
            pid = self.sock.read(2)
            pid = pid[0] << 8 | pid[1]
            sz -= 2
        msg = self.sock.read(sz)

        self.sock.settimeout(self.timeout)

        if self.cb:
            self.cb(topic, msg)

        if op & 6 == 2:
            pkt = bytearray(b"\x40\x02\0\0")
            struct.pack_into("!H", pkt, 2, pid)
            self.write(pkt)
        elif op & 6 == 4:
            return None



