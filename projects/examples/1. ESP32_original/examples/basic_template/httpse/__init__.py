import gc
import time

from uos import stat
from json import dumps

import logging
import uasyncio as asyncio

log = logging.getLogger("HTTPse")
log.setLevel(logging.INFO)

class HTTPSE:

    _mimeTypes = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".ico": "image/x-icon"
    }

    def __init__(self, port=80, web_path="/www", route_handlers=None):

        self.port = port
        self.addr = None
        self._webPath = web_path
        self._routeHandlers = route_handlers
        self.run = False

    async def server(self, reader, writer):

        addr = writer.get_extra_info('peername')
        log.info("+ from {}".format(addr))

        request = False
        try:
            request = await reader.read()
        except Exception as err:
            log.error(err)
            pass

        if not request:
            log.debug("no data, break")
            await writer.aclose()
        else:

            elements = request.decode().split()

            # log.debug("Reguest Elements {}".format(elements))

            _method = None
            _resPath = None
            _queryParams = {}

            # get method and path.
            if len(elements) > 1:
                _method = elements[0].upper()
                path = elements[1]
                elements = path.split('?', 1)

                log.debug("--> _method : {}".format(_method))
                log.debug("--> Elements : {}".format(elements))

                # get resource command
                if len(elements) > 0:
                    _resPath = elements[0]
                    log.debug("--> _resPath : {}".format(_resPath))

                    # get query and params
                    if len(elements) > 1:
                        _queryString = elements[1]
                        elements = _queryString.split('&')
                        log.debug("--> Get query : {}".format(_queryString))

                        for s in elements:
                            param = s.split('=', 1)

                            if len(param) > 0:
                                value = param[1] if len(param) > 1 else ''
                                _queryParams[param[0]] = value

                        log.debug("--> _queryParams : {}".format(_queryParams))

            log.info("= handler: {}".format(elements))
            await self.handler(_method, _resPath, _queryParams, writer.awrite )



        # log.info("<--Read reguest {}".format(read))
        # log.debug("<-- Write response")
        # await writer.awrite("HTTP/1.0 200 OK\r\n\r\nHello.\r\n")
        # log.debug("After response write")


        await writer.aclose()
        log.info("- from {}".format(addr))



    async def handler(self, _method, _res_path,  _query_params, awriter):
        # get handler function from init
        route_handler = self._get_route_handler(_res_path, _method)
        log.debug("-- route_handler : {}".format(route_handler))

        if route_handler:  # if exit run function esle try load files
            result = route_handler(_res_path, _query_params)
            content = None

            if result:
                content = dumps(result).encode()

            content_length = len(content) if content else 0

            await self._writeFirstLine(awriter, 200)

            if content_length > 0:
                await self._writeContentTypeHeader(awriter, "application/json", "UTF-8")
                await self._writeHeader(awriter, "Content-Length", content_length)

            await self._writeHeader(awriter, "Server", "uPy SeHttp")
            await self._writeHeader(awriter, "Connection", "close")
            await self._writeEndHeader(awriter)

            if content_length > 0:
                await awriter(content)

            log.debug("== Route Handler : {}".format(content))


        else:
            # if self._method.upper() == "GET":
            filepath = self._phys_path_from_url(_res_path)

            log.debug("== File Path : {}".format(filepath))

            send = False
            if filepath:
                send = await self._write_response_file(awriter, filepath)

            if not send:
                await self._writeFirstLine(awriter, 200)
                await self._writeHeader(awriter, "Server", "uPy SeHttp")
                await self._writeHeader(awriter, "Connection", "close")
                await self._writeEndHeader(awriter)


    async  def _write_response_file(self, awriter, filepath):

        content_type = self.GetMimeTypeFromFilename(filepath)
        size = stat(filepath)[6]

        if content_type and size > 0:

            with open(filepath, 'rb') as file:

                await self._writeFirstLine(awriter, 200)
                await self._writeContentTypeHeader(awriter, content_type)
                await self._writeHeader(awriter, "Content-Length", size)
                await self._writeHeader(awriter, "Server", "uPy SeHttp")
                await self._writeEndHeader(awriter)

                buf = self._try_alloc_byte_array(1024)

                if buf:
                    while size > 0:
                        x = file.readinto(buf)
                        if x < len(buf):
                            buf = memoryview(buf)[:x]

                        await awriter(buf, 0, x)

                        size -= x

                return True
        else:
            return False



    def GetMimeTypeFromFilename(self, filename):
        filename = filename.lower()
        for ext in self._mimeTypes :
            if filename.endswith(ext) :
                return self._mimeTypes[ext]
        return None

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

    def _phys_path_from_url(self, url_path):
        if url_path == '/':
            phys_path = self._webPath + '/index.html'
            if self._file_exists(phys_path):
                return phys_path
        else:
            phys_path = self._webPath + url_path
            if self._file_exists(phys_path):
                return phys_path
        return None



    async def _writeFirstLine(self, awrite, code):
        reason = "OK"
        await awrite("HTTP/1.0 %s %s\r\n" % (code, reason))

    async def _writeContentTypeHeader(self, awriter, content_type, charset=None):
        if content_type:
            ct = content_type + (("; charset={}".format(charset)) if charset else "")
        else:
            ct = "application/octet-stream"
        await self._writeHeader(awriter, "Content-Type", ct)

    async def _writeHeader(self, awriter, name, value):
        await awriter("{}: {}\r\n".format(name, value))



    async def _writeEndHeader(self, awriter):
        await  awriter("\r\n")


    def _get_route_handler(self, res_path, method):
        if self._routeHandlers:
            if method:
                method = method.upper()
                for route in self._routeHandlers:
                    if len(route) == 3 and route[0] == res_path and route[1].upper() == method:
                        return route[2]
        return None



    def start(self, addr="0.0.0.0"):

        if not self.run:
            self.addr = addr

            loop = asyncio.get_event_loop()
            loop.create_task(asyncio.start_server(self.server, self.addr, self.port))

            log.info("Run on = {}:{}".format(self.addr, self.port))

            self.run = True

        return True
