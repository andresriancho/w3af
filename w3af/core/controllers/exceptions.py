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


class BaseFrameworkException(Exception):
    """
    A small class that defines a BaseFrameworkException.
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = str(value)

    def __str__(self):
        return self.value


class RunOnce(Exception):
    """
    A small class that defines an exception to be raised by plugins that
    dont want to be run anymore.
    """
    def __init__(self, value=''):
        Exception.__init__(self)
        self.value = str(value)

    def __str__(self):
        return self.value


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
    pass


class ScanMustStopOnUrlError(ScanMustStopException):

    def __init__(self, urlerr, req):
        # Call parent's __init__
        ScanMustStopException.__init__(self, urlerr)
        self.req = req

    def __str__(self):
        error_fmt = "Extended URL library error '%s' while requesting '%s'."
        return (error_fmt % (self.msg, self.req.get_full_url()))

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

        for error_str, parsed_traceback in self.errs:
            _str += '\n' + error_str + ' ' + str(parsed_traceback)

        return _str


class ProxyException(BaseFrameworkException):
    """
    A small class that defines a w3af Proxy Exception.
    """
    pass


class DBException(BaseFrameworkException):
    pass


class FileException(BaseFrameworkException):
    pass


class OSDetectionException(BaseFrameworkException):
    pass