import socket
import network
import uos
import errno
# from socket import socket as msocket
import uio


last_client_socket = None
server_socket = None

class TelnetIO(uio.IOBase):

    def __init__(self, socket):
        self.socket = socket
        self.discard_count = 0
        self.hello()
        self.accept = 0
        self.c_pwd = ''
        self.pwd = 'micro'


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
                    raise

        if not self.accept:
            if b == b'\x03':
                self.close()
                return None

            if b == b'\r':
                if self.pwd == self.c_pwd:
                    self.accept = 1
                    self.socket.write(b"Welcome")
                    self.socket.write(b"\r\n")
                else:
                    self.socket.write(b"Wrong Password")
                    self.socket.write(b"\r\n")
                    self.c_pwd = ''
            else:
                self.c_pwd += bytes(b).decode()

            #print(b)
            return None

        return readbytes



    def write(self, data):
        # print("Socket Write")
        # return None
        # we need to write all the data but it's a non-blocking socket
        # so loop until it's all written eating EAGAIN exceptions
        if self.accept:
            while len(data) > 0:
                try:
                    written_bytes = self.socket.write(data)
                    data = data[written_bytes:]
                except OSError as e:
                    if len(e.args) > 0 and e.args[0] == errno.EAGAIN:
                        # can't write yet, try again
                        pass
                    else:
                        # something else...propagate the exception
                        raise


    def close(self):
        self.c_socket.close()


# Attach new clients to dupterm and
# send telnet control characters to disable line mode
# and stop local echoing
def accept_telnet_connect(telnet_server):
    global last_client_socket

    if last_client_socket:
        # close any previous clients
        uos.dupterm(None)
        last_client_socket.close()

    last_client_socket, remote_addr = server_socket.accept()
    print("Telnet connection from:", remote_addr)
    last_client_socket.setblocking(False)
    last_client_socket.setsockopt(socket.SOL_SOCKET, 20, uos.dupterm_notify)

    last_client_socket.sendall(bytes([255, 252, 34]))  # dont allow line mode
    last_client_socket.sendall(bytes([255, 251, 1]))  # turn off local echo



    uos.dupterm(TelnetIO(last_client_socket))


def stop():
    global server_socket, last_client_socket
    uos.dupterm(None)
    if server_socket:
        server_socket.close()
    if last_client_socket:
        last_client_socket.close()


# start listening for telnet connections on port 23
def start(port=23):
    stop()
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    ai = socket.getaddrinfo("0.0.0.0", port)
    addr = ai[0][4]

    server_socket.bind(addr)
    server_socket.listen(1)
    server_socket.setsockopt(socket.SOL_SOCKET, 20, accept_telnet_connect)

    for i in (network.AP_IF, network.STA_IF):
        wlan = network.WLAN(i)
        if wlan.active():
            print("Telnet server started on {}:{}".format(wlan.ifconfig()[0], port))