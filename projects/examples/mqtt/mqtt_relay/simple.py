import usocket as socket
import ustruct as struct
#from ubinascii import hexlify

# class MQTTException(Exception):
#     pass

class MQTTClient:

    def __init__(self, client_id, server, port=0, user=None, password=None, keepalive=0,
                 ssl=False, ssl_params={}, timeout=1, sbt=None, debug=False):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = client_id
        self.sock = None
        self.addr = socket.getaddrinfo(server, port)[0][-1]
        self.ssl = ssl
        self.ssl_params = ssl_params
        self.pid = 0
        self.cb = None
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        # self.lw_topic = None
        # self.lw_msg = None
        # self.lw_qos = 0
        # self.lw_retain = False
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
            # print(e)
            return None
        # print(write)
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

    # def set_last_will(self, topic, msg, retain=False, qos=0):
    #     if topic:
    #         self.lw_topic = topic
    #         self.lw_msg = msg
    #         self.lw_qos = qos
    #         self.lw_retain = retain

    def sock_connect(self):
        self.sock = socket.socket()
        self.sock.settimeout(self.timeout)
        # self.sock.setblocking(0)

    def connect(self, clean_session=True):

        if not self.sock:
            self.sock_connect()

        try:
            self.sock.connect(self.addr)
        except OSError as e:
            return None

        if self.ssl:
            import ussl
            self.sock = ussl.wrap_socket(self.sock, **self.ssl_params)
        msg = bytearray(b"\x10\0\0\x04MQTT\x04\x02\0\0")
        msg[1] = 10 + 2 + len(self.client_id)
        msg[9] = clean_session << 1
        if self.user is not None:
            msg[1] += 2 + len(self.user) + 2 + len(self.pswd)
            msg[9] |= 0xC0
        if self.keepalive:
            if self.keepalive > 65536:
                return None
            msg[10] |= self.keepalive >> 8
            msg[11] |= self.keepalive & 0x00FF
        # if self.lw_topic:
        #     msg[1] += 2 + len(self.lw_topic) + 2 + len(self.lw_msg)
        #     msg[9] |= 0x4 | (self.lw_qos & 0x1) << 3 | (self.lw_qos & 0x2) << 3
        #     msg[9] |= self.lw_retain << 5


        self.write(msg)

        self._send_str(self.client_id)

        # if self.lw_topic:
        #     self._send_str(self.lw_topic)
        #     self._send_str(self.lw_msg)

        if self.user is not None:
            self._send_str(self.user)
            self._send_str(self.pswd)

        resp = None
        try:
            resp = self.sock.read(4)
        except OSError as e:
            # print(e)
            return None

        # print(resp)
        # assert resp[0] == 0x20 and resp[1] == 0x02
        #
        # if resp[3] != 0:
        #     raise MQTTException(resp[3])
        #
        # result = resp[2] & 1
        #
        # return result

    def disconnect(self):

        try:
            self.sock.write(b"\xe0\0")
        except OSError as e:
            print(e)
        self.sock.close()

    # def ping(self):
    #
    #     if self.ping_status == 0 or self.ping_status == 1:
    #         self.ping_status = 0
    #         self.write(b"\xc0\0")
    # if self.debug:
    #     print("socket %s" % r1)

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
        #print(hex(len(pkt)), hexlify(pkt, ":"))
        self.write(pkt, i + 1)
        self._send_str(topic)
        # if qos > 0:
        #     self.pid += 1
        #     pid = self.pid
        #     struct.pack_into("!H", pkt, 0, pid)
        #     self.sock.write(pkt, 2)
        self.write(msg)
        # if qos == 1:
        #     while 1:
        #         op = self.check_msg() ###check_msg()   op = self.wait_msg()
        #         if op == 0x40:
        #             sz = self.sock.read(1)
        #             assert sz == b"\x02"
        #             rcv_pid = self.sock.read(2)
        #             rcv_pid = rcv_pid[0] << 8 | rcv_pid[1]
        #             if pid == rcv_pid:
        #                 return
        # elif qos == 2:
        #     assert 0
        return 1

    def subscribe(self, topic, qos=0):

        if self.cb:
            pkt = bytearray(b"\x82\0\0\0")
            self.pid += 1
            struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
            #print(hex(len(pkt)), hexlify(pkt, ":"))
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

    # Wait for a single incoming MQTT message and process it.
    # Subscribed messages are delivered to a callback previously
    # set by .set_callback() method. Other (internal) MQTT
    # messages processed internally.
    def wait_msg(self):

        try:
            self.sock.settimeout(0)
            res = self.sock.read(1)
        except OSError as e:
            return None

        if res is None or res == b"":
            return None


        # if res == b"\xd0":  # PINGRESP
        #     #sz = self.sock.read(1)[0]
        #     sz = self.sock.read(1)[0]
        #     self.ping_status = 1
        #     print(sz)
        #     return None

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

        self.cb(topic, msg)
        if op & 6 == 2:
            pkt = bytearray(b"\x40\x02\0\0")
            struct.pack_into("!H", pkt, 2, pid)
            self.write(pkt)
        elif op & 6 == 4:
            return None



