import httplib

from w3af.core.data.constants.response_codes import NO_CONTENT
from w3af.core.data.kb.config import cf


def close_on_error(read_meth):
    """
    Decorator function. When calling decorated `read_meth` if an error occurs
    we'll proceed to invoke `inst`'s close() method.
    """
    def new_read_meth(inst):
        try:
            return read_meth(inst)
        except httplib.HTTPException:
            inst.close()
            raise
    return new_read_meth


class HTTPResponse(httplib.HTTPResponse):
    # we need to subclass HTTPResponse in order to
    # 1) add readline() and readlines() methods
    # 2) add close_connection() methods
    # 3) add info() and geturl() methods

    # in order to add readline(), read must be modified to deal with a
    # buffer.  example: readline must read a buffer and then spit back
    # one line at a time.  The only real alternative is to read one
    # BYTE at a time (ick).  Once something has been read, it can't be
    # put back (ok, maybe it can, but that's even uglier than this),
    # so if you THEN do a normal read, you must first take stuff from
    # the buffer.

    # the read method wraps the original to accommodate buffering,
    # although read() never adds to the buffer.
    # Both readline and readlines have been stolen with almost no
    # modification from socket.py

    def __init__(self, sock, debuglevel=0, strict=0, method=None):
        httplib.HTTPResponse.__init__(self, sock, debuglevel, strict=strict,
                                      method=method)
        self.fileno = sock.fileno
        self.code = None
        self._rbuf = ''
        self._rbufsize = 8096
        self._handler = None     # inserted by the handler later
        self._host = None        # (same)
        self._url = None         # (same)
        self._connection = None  # (same)
        self._method = method
        self._multiread = None
        self._encoding = None
        self._time = None

    def geturl(self):
        return self._url

    URL = property(geturl)

    def get_encoding(self):
        return self._encoding

    def set_encoding(self, enc):
        self._encoding = enc

    encoding = property(get_encoding, set_encoding)

    def set_wait_time(self, t):
        self._time = t

    def get_wait_time(self):
        return self._time

    def _raw_read(self, amt=None):
        """
        This is the original read function from httplib with a minor
        modification that allows me to check the size of the file being
        fetched, and throw an exception in case it is too big.
        """
        if self.fp is None:
            return ''

        max_file_size = cf.get('max_file_size') or None
        if max_file_size:
            if self.length > max_file_size:
                self.status = NO_CONTENT
                self.reason = 'No Content'  # Reason-Phrase
                self.close()
                return ''

        if self.chunked:
            return self._read_chunked(amt)

        if amt is None:
            # unbounded read
            if self.length is None:
                s = self.fp.read()
            else:
                s = self._safe_read(self.length)
                self.length = 0
            self.close()        # we read everything
            return s

        if self.length is not None:
            if amt > self.length:
                # clip the read to the "end of response"
                amt = self.length

        # we do not use _safe_read() here because this may be a .will_close
        # connection, and the user is reading more bytes than will be provided
        # (for example, reading in 1k chunks)
        s = self.fp.read(amt)
        if self.length is not None:
            self.length -= len(s)

        return s

    def close(self):
        # First call parent's close()
        httplib.HTTPResponse.close(self)
        if self._handler:
            self._handler._request_closed(self._connection)

    def close_connection(self):
        self._handler._remove_connection(self._host, self._connection)
        self.close()

    def info(self):
        # pylint: disable=E1101
        return self.headers
        # pylint: enable=E1101

    @close_on_error
    def read(self, amt=None):
        # w3af does always read all the content of the response, and I also need
        # to do multiple reads to this response...
        #
        # BUGBUG: Is this OK? What if a HEAD method actually returns something?!
        if self._method == 'HEAD':
            # This indicates that we have read all that we needed from the socket
            # and that the socket can be reused!
            #
            # This like fixes the bug with title "GET is much faster than HEAD".
            # https://sourceforge.net/tracker2/?func=detail&aid=2202532&group_id=170274&atid=853652
            self.close()
            return ''

        if self._multiread is None:
            #read all
            self._multiread = self._raw_read()

        if not amt is None:
            L = len(self._rbuf)
            if amt > L:
                amt -= L
            else:
                s = self._rbuf[:amt]
                self._rbuf = self._rbuf[amt:]
                return s
        else:
            s = self._rbuf + self._multiread
            self._rbuf = ''
            return s

    def readline(self, limit=-1):
        i = self._rbuf.find('\n')
        while i < 0 and not (0 < limit <= len(self._rbuf)):
            new = self._raw_read(self._rbufsize)
            if not new:
                break
            i = new.find('\n')
            if i >= 0:
                i += len(self._rbuf)
            self._rbuf = self._rbuf + new
        if i < 0:
            i = len(self._rbuf)
        else:
            i += 1
        if 0 <= limit < len(self._rbuf):
            i = limit
        data, self._rbuf = self._rbuf[:i], self._rbuf[i:]
        return data

    @close_on_error
    def readlines(self, sizehint=0):
        total = 0
        line_list = []
        while 1:
            line = self.readline()
            if not line:
                break
            line_list.append(line)
            total += len(line)
            if sizehint and total >= sizehint:
                break
        return line_list

    def set_body(self, data):
        """
        This was added to make my life a lot simpler while implementing mangle
        plugins
        """
        self._multiread = data
