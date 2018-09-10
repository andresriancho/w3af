# -*- coding: utf-8 -*-
"""
headers.py

Copyright 2012 Andres Riancho

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
import string

from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.dc.generic.nr_kv_container import NonRepeatKeyValueContainer
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.dc.utils.token import DataToken


class Headers(NonRepeatKeyValueContainer):
    """
    This class represents the set of HTTP request headers.

    :author: Javier Andalia (jandalia AT gmail DOT com)
    """
    def __init__(self, init_val=(), encoding=UTF8):
        cleaned_vals = self.clean_values(init_val)

        super(Headers, self).__init__(cleaned_vals,
                                      encoding,
                                      relaxed_order=True)

    def get_type(self):
        return 'Headers'

    @classmethod
    def from_string(cls, headers_str):
        """
        :param headers_str: A string with the HTTP headers, example:
            Server: Apache
            Content-Length: 123
        """
        res = []
        split_str = headers_str.split('\r\n')
        for one_header_line in split_str:
            
            if not one_header_line:
                continue
            
            name, value = one_header_line.split(':', 1)
            
            # Escape the space after the ":"
            value = value[1:]
            
            res.append((name, value))
        
        return cls(res)

    def to_dict(self):
        """
        :return: A dictionary with lower-case key-headers and un-modified values
        """
        return dict([(k.lower(), v) for k, v in self.iteritems()])

    def clean_values(self, init_val):
        if isinstance(init_val, NonRepeatKeyValueContainer)\
        or isinstance(init_val, dict):
            return init_val

        cleaned_vals = []

        # Cleanup whatever came from the wire into a unicode string
        for key, value in init_val:
            # I can do this (key, value) thing because the headers do NOT
            # have multiple header values like query strings and post-data
            if isinstance(value, basestring):
                value = smart_unicode(value)
            
            cleaned_vals.append((smart_unicode(key), value))
        
        return cleaned_vals

    def tokens_to_value(self):
        """
        Sometimes we need to serialize the headers into a more simple form,
        a dict for example, in order to send it to msgpack. Since DataTokens
        are "complex" classes which msgpack knows nothing about, we need to
        replace any of those instances with their value.

        :return: None. We're modifying self.
        """
        for key, val, path, setter in self.iter_setters():
            if isinstance(val, DataToken):
                setter(val.get_value())

    def iget(self, header_name, default=None):
        """
        :param header_name: The name of the header we want the value for
        :param default: The default value to return if the header_name is not found
        :return: The value for a header given a name (be case insensitive)
        """
        lower = string.lower
        lower_header_name = lower(header_name)

        for stored_header_name, value in self.iteritems():
            if lower_header_name == lower(stored_header_name):
                return value, stored_header_name

        return default, None

    def icontains(self, header_name):
        """
        :param header_name: The header name to check (case insensitive)
        :return: True if the header name exists in this headers set
        """
        value, stored_header_name = self.iget(header_name)
        return True if value is not None else False

    def getheaders(self, header_name):
        """
        This is just a shortcut to iget plus some extras to make this Header
        class inter-exchangeable with the urllib2 / headers.

        https://github.com/andresriancho/w3af/issues/10769

        :param header_name: The header name to query
        :return: A list with the header values
        """
        header_value, stored_header_name = self.iget(header_name)
        if header_value is None:
            return []

        return [header_value]

    def idel(self, header_name):
        """
        :raises: KeyError when the header_name is not found in self.
        """
        _, sensitive_header_name = self.iget(header_name)
        del self[sensitive_header_name]

    # pylint: disable=E0102
    def __setitem__(self, k, v):
        if isinstance(k, basestring):
            k = smart_unicode(k, encoding=self.encoding)
        else:
            raise ValueError('Header name must be a string.')

        if isinstance(v, basestring):
            v = smart_unicode(v, encoding=self.encoding)
        elif isinstance(v, DataToken):
            encoded_str = smart_unicode(v.get_value(), encoding=self.encoding)
            v.set_value(encoded_str)
        else:
            raise ValueError('Header value must be a string.')

        super(Headers, self).__setitem__(k, v)
    # pylint: enable=E0102

    def __str__(self):
        """
        After getting some strange encoding errors I started to research about
        HTTP header encoding a little bit. The RFC mentions that special chars
        should be encoded using in RFC 2047, which in python is achieved with:
        
            >>> from email.header import Header
            >>> h = Header()
            >>> h.append(u'á')
            >>> h.encode()
            '=?utf-8?b?w4PCoQ==?='
 
        Also tested wget and curl:
            wget --header "X-MyHeader: à" moth
            curl --header "X-MyHeader: à" moth
        
        And realized that both send the special char using a "simple" unicode
        encoding (which actually goes against the RFC).
        
        Afterwards I created a test script in PHP, hosted it in my local Apache
        and analyzed what PHP got in each case. The test proved that neither
        PHP nor Apache decode the RFC 2047 and they DO ACCEPT the unicode
        encoded char.
        
        To be sure we can send HTTP requests with special chars, which are
        then correctly read by Apache/PHP, we're going to mimic wget/curl.
        
        :return: string representation of the Headers() object.
        """
        header_str_unicode = self._to_str_with_separators(u': ', u'\r\n')
        if header_str_unicode:
            header_str_unicode += u'\r\n'

        return header_str_unicode.encode('utf-8')

    def __unicode__(self):
        """
        :see: __str__ documentation.
        """
        headers_unicode = self._to_str_with_separators(u': ', u'\r\n')
        if headers_unicode:
            headers_unicode += u'\r\n'
        return headers_unicode
