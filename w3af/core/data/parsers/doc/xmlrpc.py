"""
xmlrpc.py

Copyright 2009 Andres Riancho

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
import xml.sax
import cgi
import base64

from xml.sax.handler import ContentHandler
from ruamel.ordereddict import ordereddict as OrderedDict

from w3af.core.data.dc.utils.token import DataToken


BASE_64 = 'base64'
FUZZABLE_TYPES = (BASE_64, 'string', 'name')
ALL_TYPES = ('i4', 'int', 'boolean', 'dateTime.iso8601', 'double')


class XmlRpcReadHandler(ContentHandler):
    """
    Parse a XMLRPC request and save the fuzzable parameters in
    self.fuzzable_parameters.

    The user should call this function parse_xmlrpc and build_xmlrpc.
    The rest is for internal use.
    """
    def __init__(self):
        ContentHandler.__init__(self)

        # The result
        self.fuzzable_parameters = []
        self.all_parameters = []

        # Internal variables
        self._inside_fuzzable = False

    def startElement(self, name, attrs):
        if name in FUZZABLE_TYPES:
            self._inside_fuzzable = True
            self.fuzzable_parameters.append([name.lower(), ''])

        self.all_parameters.append([name.lower(), ''])

    def characters(self, ch):
        if self._inside_fuzzable:
            self.fuzzable_parameters[-1][1] += ch

    def endElement(self, name):
        self._inside_fuzzable = False

    def get_data_container(self):
        """
        :return: An OrderedDict ready to use in the fuzzer, which is based
                 on the self._fuzzable_parameters attribute. You'll need to
                 process an XML before accessing this method, else the result
                 will be empty.
        """
        init_val = OrderedDict()

        for name, value in self.fuzzable_parameters:
            value_list = init_val.setdefault(name, [])

            if name == BASE_64:
                value_list.append(base64.b64decode(value))
            else:
                value_list.append(value)

        return init_val


class XmlRpcWriteHandler(ContentHandler):
    """
    Parse a XMLRPC request and save the fuzzable parameters in
    self.fuzzable_parameters.

    The user should call this function parse_xmlrpc and build_xmlrpc. The rest
    is for internal use.
    """
    def __init__(self, data_container):
        ContentHandler.__init__(self)

        # The resulting XML string
        self.fuzzed_xml_string = ''

        # Internal variables
        self._inside_fuzzable = False
        self._fuzzable_index = -1
        self._fuzzed_parameters = []

        # Flatten the OrderedDict to easily iterate it with startElement
        for key, value_list in data_container.items():
            for value in value_list:
                self._fuzzed_parameters.append((key, value))

    def startElement(self, name, attrs):
        if name in FUZZABLE_TYPES:
            self._inside_fuzzable = True
            self._fuzzable_index += 1

        self.fuzzed_xml_string += '<%s' % name

        for attr_name in attrs.getNames():
            self.fuzzed_xml_string += ' %s="%s"' % (attr_name,
                                                    attrs.getValue(attr_name))

        self.fuzzed_xml_string += '>'

    def characters(self, ch):
        if self._inside_fuzzable:

            modified_value = self._fuzzed_parameters[self._fuzzable_index][1]

            if isinstance(modified_value, DataToken):
                modified_value = modified_value.get_value()

            if self._fuzzed_parameters[self._fuzzable_index][0] == 'base64':
                enc_val = base64.b64encode(modified_value)
            else:
                enc_val = cgi.escape(modified_value).encode('ascii',
                                                            'xmlcharrefreplace')

            self.fuzzed_xml_string += enc_val

        else:
            self.fuzzed_xml_string += ch

    def endElement(self, name):
        self._inside_fuzzable = False
        self.fuzzed_xml_string += '</%s>' % name


def parse_xmlrpc(xml_string):
    """
    The user should call these functions: parse_xmlrpc and build_xmlrpc.

    :param xml_string: The original XML string that we got from the browser.

    :return: A handler that can then be used to access the result information
             from:
                    - handler.fuzzable_parameters
                    - handler.all_parameters
                    - handler.get_data_container
    """
    handler = XmlRpcReadHandler()
    xml.sax.parseString(xml_string, handler)
    return handler


def build_xmlrpc(xml_string, fuzzed_parameters):
    """
    The user should call these functions: parse_xmlrpc and build_xmlrpc.

    :param xml_string: The original XML string that we got from the browser.

    :param fuzzed_parameters: The ordered list which came from XmlRpcReadHandler
                              .get_data_container

    :return: The string with the new XMLRPC call to be sent to the server.
    """
    handler = XmlRpcWriteHandler(fuzzed_parameters)
    xml.sax.parseString(xml_string, handler)
    return handler.fuzzed_xml_string
