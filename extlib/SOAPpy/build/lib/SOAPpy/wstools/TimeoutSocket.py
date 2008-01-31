"""Based on code from timeout_socket.py, with some tweaks for compatibility.
   These tweaks should really be rolled back into timeout_socket, but it's
   not totally clear who is maintaining it at this point. In the meantime,
   we'll use a different module name for our tweaked version to avoid any
   confusion.

   The original timeout_socket is by:

	Scott Cotton <scott@chronis.pobox.com>
	Lloyd Zusman <ljz@asfast.com>
	Phil Mayes <pmayes@olivebr.com>
	Piers Lauder <piers@cs.su.oz.au>
	Radovan Garabik <garabik@melkor.dnp.fmph.uniba.sk>
"""

ident = "$Id: TimeoutSocket.py,v 1.2 2003/05/20 21:10:12 warnes Exp $"

import string, socket, select, errno

WSAEINVAL = getattr(errno, 'WSAEINVAL', 10022)


class TimeoutSocket:
    """A socket imposter that supports timeout limits."""

    def __init__(self, timeout=20, sock=None):
        self.timeout = float(timeout)
        self.inbuf = ''
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = sock
        self.sock.setblocking(0)
        self._rbuf = ''
        self._wbuf = ''

    def __getattr__(self, name):
        # Delegate to real socket attributes.
        return getattr(self.sock, name)

    def connect(self, *addr):
        timeout = self.timeout
        sock = self.sock
        try:
            # Non-blocking mode
            sock.setblocking(0)
            apply(sock.connect, addr)
            sock.setblocking(timeout != 0)
            return 1
        except socket.error,why:
            if not timeout:
                raise
            sock.setblocking(1)
            if len(why.args) == 1:
                code = 0
            else:
                code, why = why
            if code not in (
                errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK
                ):
                raise
            r,w,e = select.select([],[sock],[],timeout)
            if w:
                try:
                    apply(sock.connect, addr)
                    return 1
                except socket.error,why:
                    if len(why.args) == 1:
                        code = 0
                    else:
                        code, why = why
                    if code in (errno.EISCONN, WSAEINVAL):
                        return 1
                    raise
        raise TimeoutError('socket connect() timeout.')

    def send(self, data, flags=0):
        total = len(data)
        next = 0
        while 1:
            r, w, e = select.select([],[self.sock], [], self.timeout)
            if w:
                buff = data[next:next + 8192]
                sent = self.sock.send(buff, flags)
                next = next + sent
                if next == total:
                    return total
                continue
            raise TimeoutError('socket send() timeout.')

    def recv(self, amt, flags=0):
        if select.select([self.sock], [], [], self.timeout)[0]:
            return self.sock.recv(amt, flags)
        raise TimeoutError('socket recv() timeout.')

    buffsize = 4096
    handles = 1

    def makefile(self, mode="r", buffsize=-1):
        self.handles = self.handles + 1
        self.mode = mode
        return self

    def close(self):
        self.handles = self.handles - 1
        if self.handles == 0 and self.sock.fileno() >= 0:
            self.sock.close()

    def read(self, n=-1):
        if not isinstance(n, type(1)):
            n = -1
        if n >= 0:
            k = len(self._rbuf)
            if n <= k:
                data = self._rbuf[:n]
                self._rbuf = self._rbuf[n:]
                return data
            n = n - k
            L = [self._rbuf]
            self._rbuf = ""
            while n > 0:
                new = self.recv(max(n, self.buffsize))
                if not new: break
                k = len(new)
                if k > n:
                    L.append(new[:n])
                    self._rbuf = new[n:]
                    break
                L.append(new)
                n = n - k
            return "".join(L)
        k = max(4096, self.buffsize)
        L = [self._rbuf]
        self._rbuf = ""
        while 1:
            new = self.recv(k)
            if not new: break
            L.append(new)
            k = min(k*2, 1024**2)
        return "".join(L)

    def readline(self, limit=-1):
        data = ""
        i = self._rbuf.find('\n')
        while i < 0 and not (0 < limit <= len(self._rbuf)):
            new = self.recv(self.buffsize)
            if not new: break
            i = new.find('\n')
            if i >= 0: i = i + len(self._rbuf)
            self._rbuf = self._rbuf + new
        if i < 0: i = len(self._rbuf)
        else: i = i+1
        if 0 <= limit < len(self._rbuf): i = limit
        data, self._rbuf = self._rbuf[:i], self._rbuf[i:]
        return data

    def readlines(self, sizehint = 0):
        total = 0
        list = []
        while 1:
            line = self.readline()
            if not line: break
            list.append(line)
            total += len(line)
            if sizehint and total >= sizehint:
                break
        return list

    def writelines(self, list):
        self.send(''.join(list))

    def write(self, data):
        self.send(data)

    def flush(self):
        pass


class TimeoutError(Exception):
    pass
