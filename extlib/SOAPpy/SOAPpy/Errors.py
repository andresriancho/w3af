"""
################################################################################
#
# SOAPpy - Cayce Ullman       (cayce@actzero.com)
#          Brian Matthews     (blm@actzero.com)
#          Gregory Warnes     (Gregory.R.Warnes@Pfizer.com)
#          Christopher Blunck (blunck@gst.com)
#
################################################################################
# Copyright (c) 2003, Pfizer
# Copyright (c) 2001, Cayce Ullman.
# Copyright (c) 2001, Brian Matthews.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of actzero, inc. nor the names of its contributors may
# be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
################################################################################
"""

ident = '$Id: Errors.py,v 1.5 2005/02/15 16:32:22 warnes Exp $'
from version import __version__

import exceptions

################################################################################
# Exceptions
################################################################################
class Error(exceptions.Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "<Error : %s>" % self.msg
    __repr__ = __str__
    def __call__(self):
        return (msg,)

class RecursionError(Error):
    pass

class UnknownTypeError(Error):
    pass

class HTTPError(Error):
    # indicates an HTTP protocol error
    def __init__(self, code, msg):
        self.code = code
        self.msg  = msg
    def __str__(self):
        return "<HTTPError %s %s>" % (self.code, self.msg)
    __repr__ = __str__
    def __call___(self):
        return (self.code, self.msg, )

class UnderflowError(exceptions.ArithmeticError):
    pass

