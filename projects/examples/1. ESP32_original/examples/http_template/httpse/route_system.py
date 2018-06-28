import gc

class SystemHandler:

    def __init__(self, debug=True):
        self._debug = debug
        self.route_handler = ("/system", "GET" ,self._handler)


    def _handler(self, res_path, query_params):
        response = {}

        if self._debug:
            print("Debug")

        # curl -i 'http://192.168.10.111/system?memory='
        if 'memory' in query_params:
            gc.collect()
            response['memory'] = {
                    'mem_alloc': gc.mem_alloc(),
                    'mem_free': gc.mem_free()
            }
        return response


