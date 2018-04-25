
class LedHandler:

    def __init__(self, debug=True, relay=None):
        self._debug = debug
        self._relay = relay
        self.route_handler = ("/led", "GET", self._handler)

    def _handler(self, res_path, query_params):
        response = {}

        # DEBUG curl -i 'http://192.168.10.112/led?set=&state='
        if self._debug:
            print("_queryParams =", query_params)

        if 'set' in query_params:

            set = query_params["set"]
            if set == "1" or set == "0":
                set = int(query_params["set"])
                self._relay.set_state(set)
            else:
                self._relay.change_state()

        if 'state' in query_params:
            response = {'state': self._relay.state}

        if self._debug:
            print("Response =", response)

        return response


