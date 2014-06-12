"""
multipart_container.py

Copyright 2014 Andres Riancho

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
import cgi
import StringIO

from w3af.core.data.dc.form import Form
from w3af.core.data.dc.utils.multipart import get_boundary, encode_as_multipart
from w3af.core.data.constants.encodings import DEFAULT_ENCODING


class MultipartContainer(Form):
    """
    This class represents a data container for multipart/post

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    MULTIPART_HEADER = 'multipart/form-data; boundary=%s'

    def __init__(self, init_val=(), encoding=DEFAULT_ENCODING):
        super(MultipartContainer, self).__init__(init_val=init_val,
                                                 encoding=encoding)

        self.boundary = get_boundary()

    def get_type(self):
        return 'Multipart/post'

    @staticmethod
    def is_multipart(headers):
        conttype, header_name = headers.iget('content-type', '')
        return conttype.lower().startswith('multipart/form-data')

    @classmethod
    def from_postdata(cls, headers, post_data):
        if not MultipartContainer.is_multipart(headers):
            raise ValueError('No multipart content-type header.')

        environ = {'REQUEST_METHOD': 'POST'}

        try:
            fs = cgi.FieldStorage(fp=StringIO.StringIO(post_data),
                                  headers=headers, environ=environ)
        except ValueError:
            raise ValueError('Failed to create MultipartContainer.')
        else:
            # Please note that the KeyValueContainer is just a container for
            # the information.
            #
            # When the FuzzableRequest is sent the framework calls get_data()
            # which returns a string version of this object, properly encoded
            # using multipart/form-data
            #
            # To make sure the web application properly decodes the request, we
            # also include the headers in get_headers() which include the
            # boundary
            mc = cls()

            for key in fs.list:
                if key.filename is None:
                    mc.add_input([('name', key.name), ('type', 'text'),
                                  ('value', key.file.read())])
                else:
                    mc.set_file_name(key.name, key.filename)
                    mc.add_file_input([('name', key.name)])

            return mc

    @classmethod
    def from_form(cls, form):
        mc = cls(init_val=form.items())
        mc.__dict__.update(form.__dict__)
        return mc

    def get_headers(self):
        """
        Here we return the Content-Type set to multipart/post, including the
        boundary.

        :return: A tuple list with the headers required to send the
                 self._post_data to the wire. For example, if the data is
                 url-encoded:
                    a=3&b=2

                 This method returns:
                    Content-Length: 7
                    Content-Type: application/x-www-form-urlencoded

                 When someone queries this object for the headers using
                 get_headers(), we'll include these. Hopefully this means that
                 the required headers will make it to the wire.
        """
        return [('Content-Type', self.MULTIPART_HEADER % self.boundary)]

    def __str__(self):
        return encode_as_multipart(self, self.boundary)

    def __eq__(self, other):
        """
        Boundaries in different instances make a trivial string comparison
        between two MultipartContainer impossible, in other words, this:

                str(self) == str(other)

        Is not going to work.
        """
        return self.items() == other.items()