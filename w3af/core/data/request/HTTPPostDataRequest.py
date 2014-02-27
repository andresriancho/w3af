"""
HTTPPostDataRequest.py

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
from itertools import imap

from w3af.core.controllers.misc.io import is_file_like
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.form import Form


class HTTPPostDataRequest(FuzzableRequest):
    """
    This class represents a fuzzable request that sends all variables in the
    POSTDATA. This is typically used for POST requests.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, uri, method='POST', headers=Headers(),
                 cookie=None, dc=None):

        if dc is not None and not isinstance(dc, Form):
            msg = 'The dc parameter for forms needs to be a Form instance,'\
                  'got %s instead.' % type(dc)
            TypeError(msg)

        FuzzableRequest.__init__(self, uri, method, headers, cookie, dc)

    def get_data(self):
        """
        :return: A string representation of the DataContainer. There is a
        special case, in which the DataContainer has a file inside, in which
        we return the data container as it is. This is needed by the multipart
        post handler.
        """

        # TODO: This is a hack I'm not comfortable with. There should
        # be a fancier way to do this.
        # If it contains a file then we are not interested in returning
        # its string representation
        for value in self._dc.itervalues():

            if isinstance(value, basestring):
                continue
            elif is_file_like(value) or (hasattr(value, "__iter__") and
                                         any(imap(is_file_like, value))):
                return self._dc

        # Ok, no file was found; return the string representation
        return str(self._dc)

    def get_file_vars(self):
        """
        :return: A list of postdata parameters that contain a file
        """
        if isinstance(self._dc, Form):
            return self._dc.get_file_vars()
        else:
            return []

    def __repr__(self):
        return '<postdata fuzzable request | %s | %s>' % \
            (self.get_method(), self.get_uri())
