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
from w3af.core.data.dc.utils.file_token import FileDataToken


class MultipartContainer(Form):
    """
    This class represents a data container for multipart/post

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    DATA_TOKEN_KLASS = FileDataToken

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
            # the information. When the FuzzableRequest is sent it should
            # be serialized into multipart again by the MultipartPostHandler
            # because the headers contain the multipart/form-data header
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