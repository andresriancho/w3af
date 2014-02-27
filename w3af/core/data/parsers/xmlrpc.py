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


class xmlrpc_read_handler(ContentHandler):
    """
    Parse a XMLRPC request and save the fuzzable parameters in
    self.fuzzable_parameters.

    The user should call this function parse_xmlrpc and build_xmlrpc.
    The rest if for internal use.
    """
    def __init__(self):

        # The result
        self.fuzzable_parameters = []
        self.all_parameters = []

        # Internal constants
        self._fuzzable_types = ['base64', 'string', 'name']
        self._all_types = ['i4', 'int', 'boolean',
                           'dateTime.iso8601', 'double']

        # Internal variables
        self._inside_fuzzable = False

    def startElement(self, name, attrs):

        if name in self._fuzzable_types:
            self._inside_fuzzable = True
            self.fuzzable_parameters.append([name.lower(), ''])
        else:
            self.all_parameters.append([name.lower(), ''])
        return

    def characters(self, ch):
        if self._inside_fuzzable:
            self.fuzzable_parameters[-1][1] += ch

    def endElement(self, name):
        self._inside_fuzzable = False


class xmlrpc_write_handler(ContentHandler):
    """
    Parse a XMLRPC request and save the fuzzable parameters in self.fuzzable_parameters.

    The user should call this function parse_xmlrpc and build_xmlrpc. The rest if for internal use.
    """
    def __init__(self, fuzzed_parameters):

        # The resulting XML string
        self.fuzzed_xml_string = ''

        # Internal constants
        self._fuzzable_types = ['base64', 'string', 'name']

        # Internal variables
        self._inside_fuzzable = False
        self._fuzzable_number = -1
        self._fuzzed_parameters = fuzzed_parameters

    def startElement(self, name, attrs):
        if name in self._fuzzable_types:
            self._inside_fuzzable = True
            self._fuzzable_number += 1

        self.fuzzed_xml_string += '<' + name
        for attr_name in attrs.getNames():
            self.fuzzed_xml_string += ' ' + str(
                attr_name) + '="' + str(attrs.getValue(attr_name)) + '"'
        self.fuzzed_xml_string += '>'
        return

    def characters(self, ch):
        if self._inside_fuzzable:

            modified_value = self._fuzzed_parameters[self._fuzzable_number][1]

            if self._fuzzed_parameters[self._fuzzable_number][0] == 'base64':
                encoded_value = base64.b64encode(modified_value)
            else:
                encoded_value = cgi.escape(
                    modified_value).encode("ascii", "xmlcharrefreplace")

            self.fuzzed_xml_string += encoded_value

        else:
            self.fuzzed_xml_string += ch

    def endElement(self, name):
        self._inside_fuzzable = False
        self.fuzzed_xml_string += '</' + name + '>'


def parse_xmlrpc(xml_string):
    """
    The user should call this function parse_xmlrpc and build_xmlrpc. The rest if for internal use.

    :param xml_string: The original XML string that we got from the browser.

    :return: A handler that can then be used to access the result information from:
        - handler.fuzzable_parameters
        - handler.all_parameters
    """
    handler = xmlrpc_read_handler()
    xml.sax.parseString(xml_string, handler)
    return handler


def build_xmlrpc(xml_string, fuzzed_parameters):
    """
    The user should call this function parse_xmlrpc and build_xmlrpc. The rest if for internal use.

    :param xml_string: The original XML string that we got from the browser.

    :param fuzzed_parameters: The python list with the tuples that contain the fuzzed parameters.
    This list originally came from handler.fuzzable_parameters

    :return: The string with the new XMLRPC call to be sent to the server.
    """
    handler = xmlrpc_write_handler(fuzzed_parameters)
    xml.sax.parseString(xml_string, handler)
    return handler.fuzzed_xml_string
