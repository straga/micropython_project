import gc
import socket
import time
import uselect

from    uos         import stat
from    json        import dumps

class SimpleHttp:

    _mimeTypes = {
        ".html"  : "text/html",
        ".css"   : "text/css",
        ".js"    : "application/javascript",
        ".jpg"   : "image/jpeg",
        ".png"   : "image/png",
        ".ico"   : "image/x-icon"
    }

    def __init__(self,port=80, web_path="/www", debug=False, route_handlers=None) :

        self.started = False
        self._srvAddr           = ('0.0.0.0', port)
        self._webPath           = web_path
        self._debug             = debug
        self._routeHandlers     = route_handlers
        self._poller            = uselect.poll()
        self._poller_timeout    = 1000 #ms
        self._timeout           = 30
        self.clean_up()
        self.backlog            = 0


    def clean_up(self):
        self._client_socket = None
        self._server_socket = None
        self._client_map = {}
        gc.collect()


    def _try_alloc_byte_array(self, size):
        for x in range(10):
            try:
                gc.collect()
                return bytearray(size)
            except:
                pass

        return None

    def _file_exists(self, path):
        try:
            stat(path)
            return True
        except:
            return False

    def _phys_path_from_url(self,url_path):
        if url_path == '/':
            phys_path = self._webPath + '/index.html'
            if self._file_exists(phys_path):
                return phys_path
        else:
            phys_path = self._webPath + url_path
            if self._file_exists(phys_path):
                return phys_path
        return None

    def _parse_reguest(self, request):

        elements = request.decode().split()

        self._method = None
        self._resPath = None
        self._queryParams = {}

        if len(elements) > 1: #get method and path before ?
            self._method = elements[0].upper()
            path = elements[1]
            elements = path.split('?', 1)

            if len(elements) > 0: #get resource command
                self._resPath = elements[0]

                if len(elements) > 1:
                    _queryString = elements[1]
                    elements = _queryString.split('&')

                    for s in elements:
                        param = s.split('=', 1)

                        if len(param) > 0:
                            value = param[1] if len(param) > 1 else ''
                            self._queryParams[param[0]] = value

    def _get_route_handler(self, res_url, method):
        if self._routeHandlers:
            if method:
                method = method.upper()
                for route in self._routeHandlers:
                    if len(route) == 3 and route[0] == res_url and route[1].upper() == method:
                        return route[2]
        return None

    def GetMimeTypeFromFilename(self, filename) :
        filename = filename.lower()
        for ext in self._mimeTypes :
            if filename.endswith(ext) :
                return self._mimeTypes[ext]
        return None

    def _write(self, data):
        return self._client_socket.write(data)

    def _writeFirstLine(self, code):
        reason = "OK"
        self._write("HTTP/1.0 %s %s\r\n" % (code, reason))

    def _writeContentTypeHeader(self, contentType, charset=None) :
        if contentType:
            ct = contentType \
                 + (("; charset=%s" % charset) if charset else "")
        else:
            ct = "application/octet-stream"
        self._writeHeader("Content-Type", ct)

    def _writeHeader(self, name, value):
        self._write("%s: %s\r\n" % (name, value))

    def _writeEndHeader(self) :
        self._write("\r\n")

    def _write_response_file(self, filepath):

        contentType = self.GetMimeTypeFromFilename(filepath)
        size = stat(filepath)[6]

        if contentType and size > 0:

            with open(filepath, 'rb') as file:

                self._writeFirstLine(200)
                self._writeContentTypeHeader(contentType)
                self._writeHeader("Content-Length", size)
                self._writeHeader("Server", "uPy SeHttp")
                self._writeEndHeader()

                buf = self._try_alloc_byte_array(1024)

                if buf:
                    while size > 0:
                        x = file.readinto(buf)
                        if x < len(buf):
                            buf = memoryview(buf)[:x]
                        self._client_socket.write(buf)
                        size -= x

                return True
        else:
            return False


    def handle_client(self):

        try:
            request = self._client_socket.recv(1024)
        except OSError as exc:
            self.handle_close(self._client_socket)
            return None


        # # DEBUG
        # if self._debug:
        #     print("Content = %s" % str(request))

        if request:
            self._parse_reguest(request) #Prsing reguest and writ result to self
            route_handler = self._get_route_handler(self._resPath, self._method) # get handler function from init

            # DEBUG
            if self._debug:
                print("%s = %s" % (self._resPath, self._method))
                print("route_handler = %s" % route_handler)


            if route_handler: #if exit run function esle try load files
                result = route_handler(self._resPath, self._queryParams)
                content = None

                if result:
                    content = dumps(result).encode()

                contentLength = len(content) if content else 0

                self._writeFirstLine(200)
                if contentLength > 0:
                    self._writeContentTypeHeader("application/json", "UTF-8")
                    self._writeHeader("Content-Length", contentLength)
                self._writeHeader("Server", "uPy SeHttp")
                self._writeHeader("Connection", "close")
                self._writeEndHeader()

                if contentLength > 0:
                    self._client_socket.write(content)


            else:
                # if self._method.upper() == "GET":
                filepath = self._phys_path_from_url(self._resPath)

                #DEBUG
                if self._debug:
                    print("File Path = %s" % str(filepath))

                send = False
                if filepath:
                    send = self._write_response_file(filepath)

                if not send:
                    self._writeFirstLine(200)
                    self._writeHeader("Server", "uPy SeHttp")
                    self._writeHeader("Connection", "close")
                    self._writeEndHeader()



    def handle_accept(self, client):

        #self._server_socket.settimeout(0)
        client.settimeout(0)
        try:
            client_socket, client_addr = client.accept()
        except OSError as exc:
            return False

        # DEBUG
        if self._debug:
            print("+ {}".format(client_addr))

        client_socket.settimeout(self._timeout)
        self._poller.register(client_socket, uselect.POLLIN)
        self._client_map[client_addr] = (client_socket,time.time())

    def handle_close(self, client_socket, client_addr=None):
        if client_addr is None:
            for key in self._client_map:
                if self._client_map[key][0] == client_socket:
                    client_addr = key
                    break
        # DEBUG
        if self._debug:
            print("- {}".format(client_addr))

        if client_addr:
            del self._client_map[client_addr]
            self._poller.unregister(client_socket)
            client_socket.close()


    def server_process(self) :

        #set 0 timeout for aceept time out

        if self._client_map:
            p_timeout = self._poller_timeout
        else:
            p_timeout = 0

        ready = self._poller.poll(p_timeout)
        #ready = self._poller.ipoll(1000, 1)


        for entry in ready:
            if entry[0] == self._server_socket:
                self.handle_accept(self._server_socket)
            else:
                if self._client_socket is None:
                    self._client_socket = entry[0]
                    for key in self._client_map:
                        if self._client_map[key][0] == entry[0]:
                            self._client_addr = key
                            break
                elif entry[0] != self._client_socket:
                    # Sorry we are serving another guy, please hold on...
                    continue
                if not self.handle_client():
                    self.handle_close(self._client_socket)
                    # self._handler.reset_reqbuf()
                    self._client_socket = None
                    gc.collect()
                break


        if len(ready) == 0:
            now = time.time()
            for client_addr, client_info in self._client_map.items():
                if now - client_info[1] > self._timeout:
                    self.handle_close(client_info[0], client_addr)
                    if client_info[0] == client_info[0]:
                        # self._handler.reset_reqbuf()
                        self._client_socket = None
            gc.collect()


    def start(self) :

        self._server_socket = socket.socket( socket.AF_INET,
                                      socket.SOCK_STREAM)

        self._server_socket.setsockopt( socket.SOL_SOCKET,
                                 socket.SO_REUSEADDR,
                                 1 )

        self._server_socket.bind(self._srvAddr)
        self._server_socket.listen(self.backlog)

        self._poller.register(self._server_socket, uselect.POLLIN)

        self.started = True
        print("Start SeHttp")

    def stop(self) :
        print("Try Stop SeHttp")
        self._server_socket.close()
        self.clean_up()
        self.started = False
        print("Alredy Stop SeHttp")


