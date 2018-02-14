# -*- coding: utf-8 -*-
"""
plain.py

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
from w3af.core.data.dc.generic.data_container import DataContainer
from w3af.core.data.constants.encodings import UTF8


class PlainContainer(DataContainer):
    """
    Holds any type of content-type post-data, without providing any of the cool
    features like tokenizing it for fuzzing.

    This one is mostly used when dc_from_hdrs_post can't find a good container
    for the data which comes from the wire, and so we'll just store it in this
    container.

    One of the most notable features is that it will save the content-type
    header and echo it back when serialized to send to the wire.
    """
    def __init__(self, plain_data, content_type=None, encoding=UTF8):
        super(PlainContainer, self).__init__(encoding=encoding)
        self.plain_data = plain_data
        self.content_type_header_value = content_type

    def __reduce__(self):
        args = (self.plain_data, self.content_type_header_value)
        return self.__class__, args, {'token': self.token,
                                      'encoding': self.encoding}

    def __contains__(self, item):
        return False

    def get_plain_data(self):
        return self.plain_data

    def set_plain_data(self, plain_data):
        self.plain_data = plain_data

    @classmethod
    def from_postdata(cls, headers, post_data):
        content_type, _ = headers.iget('content-type', None)
        return cls(post_data, content_type)

    def get_type(self):
        return 'Plain data container'

    def iter_setters(self):
        """
        There are no tokens! We don't know how to tokenize the data stored in a
        plan data container

        The return/yield trick is awesome!
        http://stackoverflow.com/questions/13243766/python-empty-generator-function
        """
        return
        yield

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self which is
                 shorter in length than MAX_PRINTABLE
        """
        return self.plain_data[:self.MAX_PRINTABLE]

    def is_variant_of(self, other):
        """
        :return: True if self and other are both of the same DataContainer type,
                 have the same token names, and for each token the type (int or
                 string) is the same.
        """
        hm = self.content_type_header_value == other.content_type_header_value
        dm = self.plain_data == other.plain_data
        return hm and dm

    def get_headers(self):
        """
        Override in sub-classes with care.

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
        if self.content_type_header_value:
            return [('content-type', self.content_type_header_value)]

        return []

    def __str__(self):
        """
        :return: All the data
        """
        return self.plain_data
