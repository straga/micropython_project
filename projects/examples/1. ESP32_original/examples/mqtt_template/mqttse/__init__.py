
#ver 06.23.18
#based on https://github.com/micropython/micropython-lib/blob/master/umqtt.simple/umqtt/simple.py
#remove lw, ssl and some seek
import usocket as socket
import ustruct as struct
import gc

from utime import ticks_ms, ticks_diff, sleep_ms

import logging
import uasyncio as asyncio

from uerrno import EINPROGRESS, ETIMEDOUT

log = logging.getLogger("mqttse")

BUSY_ERRORS = (EINPROGRESS, ETIMEDOUT)

class MQTTClient:

    def __init__(self, client_id, server, port=1883, user=None, password=None, keepalive=0, response_time=1, sbt=None, debug=False):

        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.pswd = password

        self.keepalive = keepalive
        self.sbt = sbt

        self.status = 0
        self.first_con = 0
        self.pid = 0
        self._response_time = response_time * 1000  # Repub if no PUBACK received (ms).

        self.sock = None
        self.cb = None

        self.mqtt_bus = {}
        self.topics = {}

        self.debug = debug

    # async def _ping(self):
    #     async with self.lock:
    #         await self._as_write(b"\xc0\0")


    def close(self):
        if self.sock is not None:
            self.sock.close()

    async def as_write(self, write_data, arg=None):

        if not self.sock:
            self.status = 0
            return None
        try:
            if arg:
                self.sock.write(write_data, arg)
            else:
                self.sock.write(write_data)
        except OSError as e:
            self.status = 0
            return None

        await asyncio.sleep_ms(20)
        return True

    async def as_send_str(self, s):
        await self.as_write(struct.pack("!H", len(s)))
        await self.as_write(s)

    def _timeout(self, t):
        return ticks_diff(ticks_ms(), t) > self._response_time

    async def _as_read(self, n, sock=None):  # OSError caught by superclass
        if sock is None:
            sock = self.sock
        data = b''

        t = ticks_ms()
        while len(data) < n:
            if self._timeout(t):
                raise OSError(-1)
            try:
                msg = sock.read(n - len(data))
            except OSError as e:  # ESP32 issues weird 119 errors here
                msg = None
                if e.args[0] not in BUSY_ERRORS:
                    self.status = 0
                    raise

            if msg == b'':  # Connection closed by host (?)
                raise OSError(-1)

            if msg is not None:  # data received
                data = b''.join((data, msg))
                t = ticks_ms()

            await asyncio.sleep_ms(200)
        return data

    # def _recv_len(self):
    #     n = 0
    #     sh = 0
    #
    #     b = self.sock.read(1)[0]
    #     n |= (b & 0x7f) << sh
    #     if not b & 0x80:
    #         return n
    #     sh += 7

    async def _recv_len(self):
        n = 0
        sh = 0
        while 1:
            res = await self._as_read(1)
            b = res[0]
            n |= (b & 0x7f) << sh
            if not b & 0x80:
                return n
            sh += 7


    def set_callback(self, f):
        self.cb = f

    def open(self):

        try:
            if self.sock:
                self.close()
            self.sock = socket.socket()
        except OSError as e:
            log.debug("ERROR open: {}".format(e))
            self.status = 0
            return False

        return True

    async def connect(self, clean_session=True):

        if self.open():
            self.status = 0
            self.sock.setblocking(False)

            try:
                addr = socket.getaddrinfo(self.server, self.port)
            except OSError as e:
                    log.debug("ERROR connect: {}".format(e))
                    return None
            await asyncio.sleep_ms(500)

            if len(addr) > 0:
                addr = addr[0][-1]
            else:
                log.debug("Addr: {}".format(addr))
                return None

            log.debug("MQTT server: {}".format(addr))

            try:
                self.sock.connect(addr)
            except OSError as e:
                if e.args[0] not in BUSY_ERRORS:
                    log.debug("ERROR connect: {}".format(e))
                    return None

                await asyncio.sleep_ms(1000)

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

            await self.as_write(premsg, i + 2)
            await self.as_write(msg)
            await self.as_send_str(self.client_id)


            if self.user is not None:
                await self.as_send_str(self.user)
                await self.as_send_str(self.pswd)

            await asyncio.sleep_ms(300)
            resp = False
            try:
                resp = await self._as_read(4)
            except OSError as e:
                self.status = 0
                log.debug("ERROR connect: {}".format(e))
                return resp

            log.debug("Respt - {}".format(resp))

            if resp and resp[1] == 2:
                self.status = 1
                self.first_con = 1

            log.debug("F12 connect: st:{} - fc{}".format(self.status, self.first_con ))

    async def subscribe(self, topic, qos=0):

        pkt = bytearray(b"\x82\0\0\0")
        self.pid += 1
        struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
        await self.as_write(pkt)
        await self.as_send_str(topic)
        await self.as_write(qos.to_bytes(1, "little"))

        op = await self.wait_msg()
        if op == 0x90:
            try:
                resp = await self._as_read(4)
            except OSError as e:
                log.debug("subscripe connect: {}".format(e))
                return None
            log.debug("subscripe - {}".format(resp))
            return None

    async def publish(self, topic, msg, retain=False, qos=0):

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

        resp = False

        resp = await self.as_write(pkt, i + 1)
        resp = await self.as_send_str(topic)
        resp = await self.as_write(msg)

        return resp


    # def _try_alloc_byte_array(self, size):
    #     for x in range(10):
    #         try:
    #             gc.collect()
    #             return bytearray(size)
    #         except:
    #             pass
    #
    #     return None



    async def wait_msg(self):
        try:
            res = await self._as_read(1)
        except OSError as e:
            # log.debug("wait_msg: {}".format(e))
            # self.status = 0
            return None

        if res is None:
            return None

        if res == b'':
            return None

        if res == b"\xd0":  # PINGRESP
            await self._as_read(1)  # Update .last_rx time
            return None


        # try:
        #     res = await self._as_read(1)
        # except OSError as e:
        #     log.debug("wait_msg: {}".format(e))
        #     # self.status = 0
        #     return None
        #
        # log.debug("wait_msg res: {}".format(res))
        #
        # if res == b"":
        #     return None
        #
        # if res is None and self.first_con == 0:
        #     self.status = 0
        #     return None
        #
        # if res is None and self.first_con == 1:
        #     self.first_con = 0
        #     return None

        op = res[0]
        if op & 0xf0 != 0x30:
            return op
        sz = await self._recv_len()
        topic_len = await self._as_read(2)
        if topic_len:
            topic_len = (topic_len[0] << 8) | topic_len[1]
            topic = await self._as_read(topic_len)
            sz -= topic_len + 2

            pid = self.pid

            if op & 6:
                pid = await self._as_read(2)

                if not pid:
                    return None

                pid = pid[0] << 8 | pid[1]
                sz -= 2

            # msg = self._try_alloc_byte_array(sz)
            msg = await self._as_read(sz)

            if msg:
                # msg = self.sock.read(sz)
                # self.sock.readinto(msg)

                # self.sock.settimeout(self.timeout)
                # self.sock.setblocking(False)

                if self.cb:
                    # self.cb(topic, bytes(msg))
                    self.cb(topic, msg)

                if op & 6 == 2:
                    pkt = bytearray(b"\x40\x02\0\0")
                    struct.pack_into("!H", pkt, 2, pid)
                    await self.as_write(pkt)
                elif op & 6 == 4:
                    return None

        return None


    async def pub_bus(self):

        if self.mqtt_bus and self.status == 1:

            for key, value in self.mqtt_bus.items():

                if self.topics[key] and value:
                    # log.debug("Message Ready: Pub: {}, {}, {}".format(key, value, self.topics[key]))

                    # result = await self.publish(topic=self.topics[key], msg=bytes(value, 'utf-8'), retain=False)

                    topic = self.topics[key]
                    msg = bytes(str(value), 'utf-8')

                    # log.debug("Message Ready: topic: {}, msg: {}".format(topic, msg))

                    result = await self.publish(topic, msg)

                    # result = await self.publish(b"devices/test/ping", "1")

                    if result:
                        self.mqtt_bus[key] = None

                    # log.debug("Result: Pub: %s" % (result))


    async def client(self):

        run = True

        while run:

            if self.status == 0:
                await self.connect()

                if self.status == 1 and self.sbt:
                    await self.subscribe(self.sbt)
                await asyncio.sleep_ms(5000)

            else:

                await self.wait_msg()
                await self.pub_bus()

                await asyncio.sleep_ms(500)

    async def _keep_alive(self):

        while True:
            if self.status == 1:
                self.mqtt_bus['ping'] = 1
            await asyncio.sleep(5)

    def run(self):

        loop = asyncio.get_event_loop()
        loop.create_task(self.client())


        self.topics['topic'] = "devices/{}/#".format(self.client_id)
        self.sbt = self.topics['topic']


        self.topics['ping'] = "devices/{}/ping".format(self.client_id)

        loop.create_task(self._keep_alive())

        log.info("Client Running")
        return True







