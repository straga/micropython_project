import _thread
import gc
import utime



class ProcessRuner:

    def __init__(self, http_server=False, debug=True):
        self._http_server = http_server
        self._debug = debug
        self._http_thread = None


    def _run_http_process(self):

        while True:
            self._http_server.server_process()
            utime.sleep_ms(300)


    def start_http(self):

        _thread.stack_size(6 * 1024)
        # gc.collect()
        self._http_thread = _thread.start_new_thread(self._run_http_process, ())



