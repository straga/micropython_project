import machine
from machine import Timer

class ProcessRuner:

    def __init__(self, http_server=False ,timer_http=False, debug = True, run_period=100 ) :

        self._timer_http = timer_http
        self._debug = debug
        self._run_period = run_period
        self._http_server = http_server
        self._http_process = self._make_http_process()

    def _make_http_process(self):
        if self._debug:
            print("Make http process")
        while True:
            self._http_server.server_process()
            yield None

    def _run_http(self):
        try:
            next(self._http_process)
        except StopIteration:
            if self._debug:
                print("StopIteration")
            machine.reset()

    def run_timer(self):
        self._timer_http.init(period=self._run_period, mode=Timer.PERIODIC, callback=lambda t: self._run_http())
