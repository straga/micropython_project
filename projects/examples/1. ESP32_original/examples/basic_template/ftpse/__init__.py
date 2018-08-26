
import logging
import uos
import uerrno
import uasyncio as asyncio
import network

log = logging.getLogger("ftpse")
log.setLevel(logging.INFO)


class FTPClient:

    def __init__(self, port=21, dport=26):

        self.port = port
        self.dport = dport
        self.max_chuck_size = 512
        self.addr = False
        self.pasv = False
        self.start = False
        self.transfer = False
        self.transfer_path = False
        self.transfer_rpl = False
        self.con_type = False


    def run(self, addr=None):

        if not addr or addr == "0.0.0.0":
            log.info("No active connection")
            return False

        self.addr = addr

        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(self.server, self.addr, self.port))

        log.info("FTP run on = %s" % self.addr)
        return True

    async def send_list_data(self, writer):

        path = uos.getcwd()
        items = uos.listdir(path)

        if path == '/':
            path = ''
        for i in items:
            file_stat = uos.stat(path + "/" + i)

            file_permissions = "drwxr-xr-x" if (file_stat[0] & 0o170000 == 0o040000) else "-rw-r--r--"
            file_size = file_stat[6]
            description = "{}    1 owner group {:>10} Jan 1 2000 {}\r\n".format(
                file_permissions, file_size, i)

            try:
                await writer.awrite(description)
            except Exception as err:
                log.error(err)
                pass

    async def send_file_data(self, writer):

        max_chuck_size = self.max_chuck_size
        buf = bytearray(max_chuck_size)

        argument = self.transfer_path
        remaining_size = uos.stat(argument)[-4]

        try:
            with open(argument, "rb") as f:
                while remaining_size:
                    chuck_size = f.readinto(buf)
                    remaining_size -= chuck_size
                    mv = memoryview(buf)
                    ret = await writer.awrite(mv[:chuck_size])
            self.transfer_rpl = "226 Transfer complete.\r\n"
        except OSError as e:
            if e.args[0] == uerrno.ENOENT:
                self.transfer_rpl = "550 No such file.\r\n"
            else:
                self.transfer_rpl = "550 Open file error.\r\n"
        finally:
            self.transfer_path = False
            del buf

        return True


    async def save_file_data(self, reader):
        max_chuck_size = self.max_chuck_size
        argument = self.transfer_path

        log.debug("Argument - {}".format(argument))

        try:
            with open(argument, "wb") as f:
                log.debug("WB")
                # f.seek(0)
                while True:
                    try:
                        data = await reader.read(max_chuck_size)
                        w = f.write(data)
                        if not data or w < max_chuck_size:
                            break

                    except Exception as e:
                        log.error("exception .. {}".format(e))

            self.transfer_rpl = "226 Transfer complete\r\n"
        except OSError as e:
            self.transfer_rpl = "550 File i/o error.\r\n"
        finally:
            self.transfer_path = False

        return True



    async def data_server(self, reader, writer):

        addr = writer.get_extra_info('peername')
        log.info("+ Data Server <- client from {}".format(addr))
        log.debug("Data Start {}".format(self.start))

        if not self.transfer:
            self.transfer = "Start"
        log.debug("Data Transfer {}".format(self.transfer))


        while True:
            if self.transfer:

                if self.transfer is "LIST":
                    log.debug("s1. List Dir")
                    await self.send_list_data(writer)
                    self.transfer = False

                if self.transfer is "SEND":
                    log.debug("s1. Send File")
                    await self.send_file_data(writer)
                    self.transfer = False

                if self.transfer is "SAVE":
                    log.debug("s1. Save File")
                    await self.save_file_data(reader)
                    self.transfer = False

                if self.transfer is "Start":
                    log.debug("s1. State Start")
                    #Time for wait Open Socker Activite if not active = Close
                    await asyncio.sleep_ms(500)
                    if self.transfer is "Start":
                        self.transfer = False


            # await asyncio.sleep_ms(300)
            if not self.transfer:
                log.info("- Data Server <- client from {}".format(addr))
                log.debug("s2. Data Server = Close")
                await writer.aclose()
                self.start = False
                break






    async def send_data(self, type):

        log.debug("SEND Type: {}".format(type))
        log.debug("SEND Transfer: {}".format(self.transfer))


        if type is "passive":
            self.start = True
            while self.start:
                #wait 100ms for next check start. Lite =100, Hard = 0
                await asyncio.sleep_ms(100)

        if type is "active":
            log.info("Active: connecting to -> %s %d" % (self.data_ip, self.data_port))
            reader, writer = await asyncio.open_connection(self.data_ip, self.data_port)

            if self.transfer is "LIST":
                log.debug("s1. List Dir")
                await self.send_list_data(writer)

            if self.transfer is "SEND":
                log.debug("s1. Send File")
                await self.send_file_data(writer)

            if self.transfer is "SAVE":
                log.debug("s1. Save File")
                await self.save_file_data(reader)


            await writer.aclose()


        log.debug("s3. Send Data Done")
        return True



    def get_absolute_path(self, cwd, payload):
        # Just a few special cases "..", "." and ""
        # If payload start's with /, set cwd to /
        # and consider the remainder a relative path
        if payload.startswith('/'):
            cwd = "/"
        for token in payload.split("/"):
            if token == '..':
                if cwd != '/':
                    cwd = '/'.join(cwd.split('/')[:-1])
                    if cwd == '':
                        cwd = '/'
            elif token != '.' and token != '':
                if cwd == '/':
                    cwd += token
                else:
                    cwd = cwd + '/' + token
        return cwd

    def get_path(self, argument):

        cwd = uos.getcwd()
        path = self.get_absolute_path(cwd, argument)
        log.debug("Get path is %s" % path)
        return path


    async def server(self, reader, writer):
        addr = writer.get_extra_info('peername')
        log.info("client from {}".format(addr))
        await writer.awrite("220 Welcome to micro FTP SE server\r\n")

        while True:

            data = False
            try:
                data = await reader.readline()
            except Exception as err:
                log.error(err)
                pass


            if not data:
                log.debug("no data, break")
                await writer.aclose()
                break
            else:
                log.debug("recv = %s" % data)

                try:
                    data = data.decode("utf-8")
                    split_data = data.split(' ')
                    cmd = split_data[0].strip('\r\n')
                    argument = split_data[1].strip('\r\n') if len(split_data) > 1 else None
                    log.debug("cmd is %s, argument is %s" % (cmd, argument))
                except Exception as err:
                    log.error(err)
                    pass

                if hasattr(self, cmd):
                    func = getattr(self, cmd)
                    result = await func(writer, argument)

                    if not result:
                        log.debug("result = None")
                        await writer.aclose()
                        break
                    log.debug("result = %d" % result)

                else:
                    await writer.awrite("520 not implement.\r\n")


    async def USER(self, stream, argument):
        #331 next step password
        # await stream.awrite("331 User Ok.\r\n")

        await stream.awrite("230 Logged in.\r\n")
        return True

    async def PASS(self, stream, argument):
        await stream.awrite("230 Passwd Ok.\r\n")
        return True

    async def SYST(self, stream, argument):
        await stream.awrite("215 UNIX Type: L8\r\n")
        return True

    async def NOOP(self, stream, argument):
        await stream.awrite("200 OK\r\n")
        return True

    async def FEAT(self, stream, argument):
        await stream.awrite("211 no-features\r\n")
        return True


    async def CDUP(self, stream, argument):
        argument = '..' if not argument else '..'
        log.debug("CDUP argument is %s" % argument)
        try:
            uos.chdir(self.get_path(argument))
            await stream.awrite("250 Okey.\r\n")
        except Exception as e:
            await stream.awrite("550 {}.\r\n".format(e))
        return True

    async def CWD(self, stream, argument):
        log.debug("CWD argument is %s" % argument)
        try:
            uos.chdir(self.get_path(argument))
            await stream.awrite("250 Okey.\r\n")
        except Exception as e:
            await stream.awrite("550 {}.\r\n".format(e))
        return True

    async def PWD(self, stream, argument):
        try:
            cwd = uos.getcwd()
            await stream.awrite('257 "{}".\r\n'.format(cwd))
        except Exception as e:
            await stream.awrite('550 {}.\r\n'.format(e))
        return True

    async def TYPE(self, stream, argument):
        #Always use binary mode 8-bit
        await stream.awrite("200 Binary mode.\r\n")
        return True

    async def MKD(self, stream, argument):

        try:
            uos.mkdir(self.get_path(argument))
            await stream.awrite("257 Okey.\r\n")
        except OSError as e:
            if e.args[0] == uerrno.EEXIST:
                await stream.awrite("257 Okey.\r\n")
            else:
                await stream.awrite("550 {}.\r\n".format(e))
        return True

    async def RMD(self, stream, argument):
        try:
            uos.rmdir(self.get_path(argument))
            await stream.awrite("257 Okey.\r\n")
        except Exception as e:
            await stream.awrite("550 {}.\r\n".format(e))
        return True

    async def SIZE(self, stream, argument):
        try:
            size = uos.stat(self.get_path(argument))[6]
            await stream.awrite('213 {}\r\n'.format(size))
        except Exception as e:
            await stream.awrite('550 {}.\r\n'.format(e))
        return True


    async def RETR(self, stream, argument):

        await stream.awrite("150 Opening data connection\r\n")

        self.transfer = "SEND"
        self.transfer_path = self.get_path(argument)
        await self.send_data(self.con_type)

        if self.transfer_rpl:
            await stream.awrite(self.transfer_rpl)
            self.transfer_rpl = False
        else:
            await stream.awrite("550 File Load Error.\r\n")

        return True



    async def STOR(self, stream, argument):

        await stream.awrite("150 Opening data connection\r\n")


        self.transfer = "SAVE"
        self.transfer_path = self.get_path(argument)
        await self.send_data(self.con_type)

        if self.transfer_rpl:
            await stream.awrite(self.transfer_rpl)
            self.transfer_rpl = False
        else:
            await stream.awrite("550 File Save Error.\r\n")


        return True



    async def QUIT(self, stream, argument):
        await stream.awrite("221 Bye!.\r\n")
        return False



    async def DELE(self, stream, argument):
        try:
            uos.remove(self.get_path(argument))
            await stream.awrite("257 Okey.\r\n")
        except Exception as e:
            await stream.awrite("550 {}.\r\n".format(e))
        return True



    async def PASV(self, stream, argument):

        result = '227 Entering Passive Mode ({},{},{}).\r\n'.format(
            self.addr.replace('.', ','), self.dport >> 8, self.dport % 256)

        await stream.awrite(result)

        if not self.pasv:
            log.info("Start Passive Data Server to %s %d" % (self.addr, self.dport))
            loop = asyncio.get_event_loop()
            loop.call_soon(asyncio.start_server(self.data_server, self.addr, self.dport))
            self.pasv = True

        self.con_type = "passive"

        return True


    async def PORT(self, stream, argument):
        argument = argument.split(',')
        self.data_ip = '.'.join(argument[:4])
        self.data_port = (int(argument[4])<<8)+int(argument[5])
        self.data_addr = (self.data_ip, self.data_port)
        log.info("got the port {}".format(self.data_addr))
        # await stream.awrite("220 Got the port.\r\n")
        await stream.awrite("200 OK.\r\n")
        self.con_type = "active"
        return True



    async def LIST(self, stream, argument):

        await stream.awrite("150 Here comes the directory listing.\r\n")

        self.transfer = "LIST"
        await self.send_data(self.con_type)

        await stream.awrite("226 Directory send okey.\r\n")

        return True

    async def MDTM(self, stream, argument):

        #Dummy for File Modification Time.
        await stream.awrite("213 {}.\r\n".format(argument))
        return True




