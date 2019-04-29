# ----------------------------------------------------------------------------------------------------------------------
# Timer Class
# ----------------------------------------------------------------------------------------------------------------------
class GlobalTimer(object):
    def __init__(self, interval=1.0):
        self._registered = set()
        self._interval = interval
        self._timer = None
        self._start_timer()

    def register_callback(self, callback):
        self._registered.add(callback)

    def unregister_callback(self, callback):
        self._registered.remove(callback)

    def _start_timer(self):
        self._timer = Timer(self._interval, self._callback)
        self._timer.start()

    def _callback(self):
        for callback in self._registered:
            callback()
        self._start_timer()