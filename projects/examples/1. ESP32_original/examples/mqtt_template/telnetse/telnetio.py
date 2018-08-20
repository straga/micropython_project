import uio
import errno


class TelnetIO(uio.IOBase):

    def __init__(self, socket, pwd='micro'):
        self.socket = socket
        self.discard_count = 0
        self.hello()
        self.accept = 0
        self.c_pwd = ''
        self.pwd = pwd


    def hello(self):

        self.socket.write(b"Hello Telnet from uPY")
        self.socket.write(b"\r\n")
        self.socket.write(b"Enter Password")
        self.socket.write(b"\r\n")


    def readinto(self, b):
        # print("Socket Readinto")
        # return None
        readbytes = 0
        for i in range(len(b)):
            try:
                byte = 0
                # discard telnet control characters and
                # null bytes
                while (byte == 0):
                    byte = self.socket.recv(1)[0]
                    if byte == 0xFF:
                        self.discard_count = 2
                        byte = 0
                    elif self.discard_count > 0:
                        self.discard_count -= 1
                        byte = 0

                b[i] = byte

                readbytes += 1
            except (IndexError, OSError) as e:
                if type(e) == IndexError or len(e.args) > 0 and e.args[0] == errno.EAGAIN:
                    if readbytes == 0:
                        return None
                    else:
                        return readbytes
                else:
                    return None

        if not self.accept:
            # print("1. ACCEPT", b)
            if b == b'\x03':
                self.close()
                return None

            if b == b'\r': #Enter detect
                if self.pwd == self.c_pwd:
                    self.accept = 1
                    self.socket.write(b"Welcome")
                    self.socket.write(b"\r\n")
                else:
                    self.socket.write(b"Wrong Password")
                    self.socket.write(b"\r\n")
                    self.c_pwd = ''
            else:

                try:
                    self.c_pwd += bytes(b).decode()
                except:
                    print("ERROR:")
                    self.c_pwd = ''
                    pass

            # print("3. exit")
            return None

        return readbytes



    def write(self, data):
        if self.accept:
            close = False
            while len(data) > 0 or close:
                try:
                    written_bytes = self.socket.write(data)
                    data = data[written_bytes:]
                except OSError as e:
                    if len(e.args) > 0 and e.args[0] == errno.EAGAIN:
                        pass
                    else:
                        close = True


    def close(self):
        self.socket.close()
