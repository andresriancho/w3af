"""
BaseFrameworkException.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
#
#   New to this code? Take a look at the exceptions documentation!
#   https://github.com/andresriancho/w3af/wiki/HTTP-error-handling-in-w3af
#


class BaseFrameworkException(Exception):
    """
    A small class that defines a BaseFrameworkException.
    """
    def __init__(self, message):
        self.value = str(message)
        Exception.__init__(self, self.value)

    def __str__(self):
        return self.value


class HTTPRequestException(BaseFrameworkException):
    """
    This exception should be raised when **one** HTTP request fails.
    """
    def __init__(self, message, request=None):
        BaseFrameworkException.__init__(self, message)
        self.request = request

    def get_url(self):
        if self.request is None:
            return None

        return self.request.get_full_url()


class ConnectionPoolException(HTTPRequestException):
    pass


class RunOnce(Exception):
    """
    A small class that defines an exception to be raised by plugins that
    run only once and then are useless
    """
    def __init__(self, value=''):
        Exception.__init__(self)
        self.value = str(value)

    def __str__(self):
        return self.value


class NoMoreCalls(RunOnce):
    """
    A small class that defines an exception to be raised by plugins that
    don't want to be run anymore.
    """
    pass


class ScanMustStopException(Exception):
    """
    If this exception is caught by the core, then it should stop the whole
    process. This exception is raised in a few places. NOT to be used
    extensively.
    """
    def __init__(self, msg, errs=()):
        self.msg = str(msg)
        self.errs = errs

    def __str__(self):
        msg = str(self.msg)
        
        if self.errs:
            msg += ' The following errors were logged:\n'
            for err in self.errs:
                msg += '  - %s' % err
                
        return msg

    __repr__ = __str__


class ScanMustStopByUserRequest(ScanMustStopException):
    """
    The user requested the scan to stop, raise this exception to stop it.
    """
    pass


class ScanMustStopOnUrlError(ScanMustStopException):
    """
    This exception should be raised when **many** HTTP requests fail.

    Please note that HTTPRequestException should be used when only one HTTP
    request failed.
    """
    def __init__(self, url_error, req):
        # Call parent's __init__
        ScanMustStopException.__init__(self, url_error)
        self.req = req

    def __str__(self):
        error_fmt = "Extended URL library error '%s' while requesting '%s'."
        return error_fmt % (self.msg, self.req.get_full_url())

    __repr__ = __str__


class ScanMustStopByKnownReasonExc(ScanMustStopException):

    def __init__(self, msg, errs=(), reason=None):
        ScanMustStopException.__init__(self, msg, errs)
        self.reason = reason

    def __str__(self):
        _str = ScanMustStopException.__str__(self)
        if self.reason:
            _str += ' - Reason: %s' % self.reason
        return _str


class ScanMustStopByUnknownReasonExc(ScanMustStopException):

    def __str__(self):
        _str = self.msg

        for error_str in self.errs:
            _str += '\n' + error_str

        return _str


class ProxyException(BaseFrameworkException):
    """
    A small class that defines a w3af Proxy Exception.
    """
    pass


class DBException(BaseFrameworkException):
    pass


class NoSuchTableException(DBException):
    pass


class MalformedDBException(DBException):
    pass


class FileException(BaseFrameworkException):
    pass


class OSDetectionException(BaseFrameworkException):
    pass


class NoVulnerabilityFoundException(BaseFrameworkException):
    pass


class ExploitFailedException(BaseFrameworkException):
    pass


class BodyCutException(BaseFrameworkException):
    pass


class FourOhFourDetectionException(BaseFrameworkException):
    pass


class ParserException(BaseFrameworkException):
    pass