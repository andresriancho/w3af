"""
xmlrpc.py

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
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.parsers.doc.xmlrpc import parse_xmlrpc, build_xmlrpc


ERR_MSG = 'Unsupported xml_data "%s" for xmlrpc container.'
XMLRPC_WORDS = ('<methodcall>', '<methodname>', '<params>',
                '</methodcall>', '</methodname>', '</params>')


class XmlRpcContainer(KeyValueContainer):
    """
    This class represents a data container for an XML-rpc request.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    XMLRPC_CONTENT_TYPE = 'text/xml'

    def __init__(self, xml_post_data, encoding=UTF8):
        """
        :param xml_post_data: The XMLRPC call as string
        """
        KeyValueContainer.__init__(self, init_val=[], encoding=encoding)

        if not isinstance(xml_post_data, basestring):
            raise TypeError(ERR_MSG % xml_post_data)

        self._xml_post_data = xml_post_data
        self.parse_xml_data(xml_post_data)

    def __reduce__(self):
        return self.__class__, (self._xml_post_data,), {'token': self.token,
                                                        'encoding': self.encoding}

    def get_type(self):
        return 'XML-RPC'

    def parse_xml_data(self, xml_post_data):
        """
        Parses the XML post data and stores all the information required to
        fuzz the XML data as attributes.

        :param xml_post_data: The XMLRPC call as string
        :raises: ValueError if the xml_post_data is not valid XML or XML-RPC
        """
        try:
            read_handler = parse_xmlrpc(xml_post_data)
        except:
            raise ValueError(ERR_MSG % xml_post_data[:50])
        else:
            # Tried to do this with self.update but it was failing :S
            for k, v in read_handler.get_data_container().items():
                self[k] = v

    @staticmethod
    def is_xmlrpc(post_data):
        return all(map(lambda stop: stop in post_data.lower(), XMLRPC_WORDS))

    @staticmethod
    def content_type_matches(headers):
        """
        TODO: I need to review the whole XML RPC implementation!
              Returning false here disables this content-type for at least
              the REST API scanner.
        """
        return False

    @classmethod
    def from_postdata(cls, headers, post_data):
        if not XmlRpcContainer.is_xmlrpc(post_data):
            raise ValueError('Failed to identify post_data as XML-RPC.')

        return cls(post_data)

    def __str__(self):
        """
        :return: string representation by writing back to XML string
        """
        return build_xmlrpc(self._xml_post_data, self)

    def get_headers(self):
        return [('Content-Type', self.XMLRPC_CONTENT_TYPE)]
