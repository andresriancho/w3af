'''
w3afException.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''

class w3afException(Exception):
    '''
    A small class that defines a w3afException.
    '''
    
    def __init__(self, value):
        Exception.__init__( self )
        self.value = str(value)
    
    def __str__(self):
        return self.value


class w3afRunOnce(Exception):
    '''
    A small class that defines an exception to be raised by plugins that
    dont want to be run anymore.
    '''
    def __init__(self, value=''):
        Exception.__init__( self )
        self.value = str(value)
    
    def __str__(self):
        return self.value

class w3afMustStopException(Exception):
    '''
    If this exception is caught by the core, then it should stop the whole 
    process. This exception is raised in a few places. NOT to be used
    extensively.
    '''
    def __init__(self, msg, errs=()):
        self.msg = str(msg)
        self.errs = errs

    def __str__(self):
        return str(self.msg) + '\n'.join( [str(e) for e in self.errs])
    
    __repr__ = __str__


class w3afMustStopOnUrlError(w3afMustStopException):
    
    def __init__(self, urlerr, req):
        reason = urlerr.reason
        if type(reason) is str:
            ec, em = None, reason
        else:
            try:
                ec, em = reason
            except ValueError:
                ec, em = None, reason[0]
        # Call parent's __init__
        w3afMustStopException.__init__(self, em)
        self.errcode = ec
        self.req = req
    
    def __str__(self):
        return ("UrlError '%s' while requesting '%s'. Error code was: %s" % 
                (self.msg, self.req.get_full_url(), self.errcode))
    
    __repr__ = __str__


class w3afMustStopByKnownReasonExc(w3afMustStopException):

    def __init__(self, msg, errs=(), reason=None):
        w3afMustStopException.__init__(self, msg, errs)
        self.reason = reason
    
    def __str__(self):
        _str = w3afMustStopException.__str__(self)
        if self.reason:
            _str += ' - Reason: %s' % self.reason
        return _str


class w3afMustStopByUnknownReasonExc(w3afMustStopException):
    
    def __str__(self):
        _str = self.msg

        for error_str, parsed_traceback in self.errs:
            _str += '\n' + error_str + ' ' + str(parsed_traceback)

        return _str


class w3afProxyException(w3afException):
    '''
    A small class that defines a w3af Proxy Exception.
    '''
    pass
