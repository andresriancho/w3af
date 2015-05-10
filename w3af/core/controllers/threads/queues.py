from multiprocessing.queues import SimpleQueue


class SimpleQueueWithSize(SimpleQueue):

    def __init__(self):
        SimpleQueue.__init__(self)
        self._qsize = 0

    def qsize(self):
        return self._qsize

    def _make_methods(self):
        recv = self._reader.recv
        racquire, rrelease = self._rlock.acquire, self._rlock.release
        def get():
            racquire()
            try:
                return recv()
            finally:
                self._qsize -= 1
                rrelease()
        self.get = get

        if self._wlock is None:
            # writes to a message oriented win32 pipe are atomic
            self.put = self._writer.send
        else:
            send = self._writer.send
            wacquire, wrelease = self._wlock.acquire, self._wlock.release
            def put(obj):
                wacquire()
                try:
                    return send(obj)
                finally:
                    self._qsize += 1
                    wrelease()
            self.put = put

