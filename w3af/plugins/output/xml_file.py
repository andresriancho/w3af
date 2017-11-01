"""
xml_file.py

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
import os
import re
import sys
import time
import base64
import xml.dom.minidom

import w3af.core.data.kb.config as cf
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.controllers.misc import get_w3af_version
from w3af.core.controllers.exceptions import BaseFrameworkException, DBException
from w3af.core.data.misc.encoding import smart_str
from w3af.core.data.db.history import HistoryItem
from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.constants.encodings import DEFAULT_ENCODING


NON_BIN = ('atom+xml', 'ecmascript', 'EDI-X12', 'EDIFACT', 'json',
           'javascript', 'rss+xml', 'soap+xml', 'font-woff',
           'xhtml+xml', 'xml-dtd', 'xop+xml')

TIME_FORMAT = '%a %b %d %H:%M:%S %Y'

# https://stackoverflow.com/questions/1707890/fast-way-to-filter-illegal-xml-unicode-chars-in-python
#
# I added (0xc3, 0xc3) to the list of banned characters after a couple of bug reports, I'm not
# really sure why but it breaks Firefox's XML parser and the character was not in the original
# list.
_illegal_unichrs = [(0x00, 0x08),
                    (0x0B, 0x0C),
                    (0x0E, 0x1F),
                    (0x7F, 0x84),
                    (0x86, 0x9F),
                    (0xc3, 0xc3),
                    (0xFDD0, 0xFDDF),
                    (0xFFFE, 0xFFFF)]

if sys.maxunicode >= 0x10000:  # not narrow build
    _illegal_unichrs.extend([(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                             (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                             (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                             (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                             (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                             (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                             (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                             (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)])

_illegal_ranges = [u'%s-%s' % (unichr(low), unichr(high)) for (low, high) in _illegal_unichrs]
INVALID_XML = re.compile(u'[%s]' % u''.join(_illegal_ranges))


def xml_str(s, replace_invalid=True):
    """
    Avoid encoding errors while generating objects' utf8 byte-string
    representations.

    Should fix issues similar to:
    https://github.com/andresriancho/w3af/issues/12924

    :param s: The input string/unicode
    :param replace_invalid: If there are invalid XML chars, replace them.
    :return: A string ready to be sent to the XML file
    """
    encoded_str = smart_str(s, encoding='utf8', errors='xmlcharrefreplace')

    if replace_invalid:
        encoded_str = INVALID_XML.sub('?', encoded_str)

    return encoded_str


class xml_file(OutputPlugin):
    """
    Print all messages to a xml file.

    :author: Kevin Denver ( muffysw@hotmail.com )
    """

    XML_OUTPUT_VERSION = '2.1'

    def __init__(self):
        OutputPlugin.__init__(self)

        # These attributes hold the file pointers
        self._file = None

        # User configured parameters
        self._file_name = '~/report.xml'
        self._timestamp = str(int(time.time()))
        self._long_timestamp = str(time.strftime(TIME_FORMAT, time.localtime()))

        # Set defaults for scan metadata
        self._plugins_dict = {}
        self._options_dict = {}

        # List with additional xml elements
        self._errors = DiskList()

        # Dict which acts as a cache to improve flush() performance
        # https://github.com/andresriancho/w3af/issues/16119
        self._xml_node_cache = DiskDict(table_prefix='xml_node_cache')

        # xml document that helps with the creation of new elements
        # this is an empty document until we want to write to the
        # output file, where we populate it, serialize it to the file,
        # and empty it again
        self._xml = None

    def _open_file(self):
        self._file_name = os.path.expanduser(self._file_name)
        try:
            self._file = open(self._file_name, 'w')
        except IOError, io:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._file_name), io.strerror)
            raise BaseFrameworkException(msg % args)
        except Exception, e:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._file_name), e)
            raise BaseFrameworkException(msg % args)

    def do_nothing(self, *args, **kwds):
        pass

    debug = information = vulnerability = console = log_http = do_nothing

    def error(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for error messages.
        """
        #
        # Note that while the call to "get_caller()" is costly, it only happens
        # when an error occurs, so it shouldn't impact performance
        #
        error_data = (message, self.get_caller())
        self._errors.append(error_data)

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        This method MUST be implemented on every plugin.

        :return: No value is returned.
        """
        self._file_name = option_list['output_file'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Output file name where to write the XML data'
        o = opt_factory('output_file', self._file_name, d, OUTPUT_FILE)
        ol.add(o)

        return ol

    def log_enabled_plugins(self, plugins_dict, options_dict):
        """
        This method is called from the output manager object. This method should
        take an action for the enabled plugins and their configuration. Usually,
        write the info to a file or print it somewhere.

        :param plugins_dict: A dict with all the plugin types and the enabled
                             plugins for that type of plugin.
        :param options_dict: A dict with the options for every plugin.
        """
        # See doc for _log_enabled_plugins_to_xml to understand why we don't write
        # to the XML just now.
        self._plugins_dict = plugins_dict
        self._options_dict = options_dict

    def end(self):
        """
        This method is called when the scan has finished.
        """
        self.flush()

        # Free some memory and disk space
        self._plugins_dict = {}
        self._options_dict = {}
        self._errors.cleanup()
        self._xml_node_cache.cleanup()

    def flush(self):
        """
        Write the XML to the output file
        :return: None
        """
        # In some rare cases the XML output plugin takes considerable
        # time to run flush(), and the output plugin will call flush()
        # a second time, while the previous flush is still running.
        #
        # This will end up in an exception like:
        #
        #       "'NoneType' object has no attribute 'createElement'"
        #
        # In order to avoid this issue I'm going to allow only one flush
        # to run at the same time. If the self._xml attribute is not None
        # it means that the first call to flush() in the other thread never
        # reached the last call to _empty_xml_root() in this method.
        if self._xml is not None:
            # We need to wait for the first call to flush() to finish
            return

        # Start from a clean state, just in case.
        self._empty_xml_root()

        try:
            self._create_root_xml_elems()
            self._log_enabled_plugins_to_xml()
            self._write_findings_to_xml()
            self._write_errors_to_xml()
            self._write_xml_to_file()
        finally:
            # Free some memory
            self._empty_xml_root()

    def _empty_xml_root(self):
        self._xml = None
        self._top_elem = None
        self._scan_info = None

    def _create_root_xml_elems(self):
        # XML root
        self._xml = xml.dom.minidom.Document()

        # The scan tag, with all vulnerabilities as child
        self._top_elem = self._xml.createElement('w3af-run')
        self._top_elem.setAttribute('start', self._timestamp)
        self._top_elem.setAttribute('start-long', self._long_timestamp)
        self._top_elem.setAttribute('version', self.XML_OUTPUT_VERSION)

        # Add in the version details
        version_element = self._xml.createElement('w3af-version')
        version = xml_str(get_w3af_version.get_w3af_version())
        version_data = self._xml.createTextNode(version)
        version_element.appendChild(version_data)
        self._top_elem.appendChild(version_element)

    def _write_xml_to_file(self):
        """
        Write xml report
        :return: None
        """
        self._open_file()
        self._xml.appendChild(self._top_elem)

        try:
            self._xml.writexml(self._file,
                               addindent=' ' * 4,
                               newl='\n',
                               encoding=DEFAULT_ENCODING)
            self._file.flush()
        finally:
            self._file.close()

    def _write_errors_to_xml(self):
        """
        Write all errors and callers to the XML output file.
        :return: None, we write the data to the XML
        """
        for message, caller in self._errors:
            message_node = self._xml.createElement('error')
            message_node.setAttribute('caller', xml_str(caller))

            description = self._xml.createTextNode(xml_str(message))
            message_node.appendChild(description)
            self._top_elem.appendChild(message_node)

    def _write_vulndb_details_to_xml(self, message_node, info):
        """
        If there is information from the vulndb, then we should write it
        to the XML

        :param message_node: The xml node
        :param info: The Info() instance with the vuln information
        :return: None
        """
        if not info.has_db_details():
            return

        desc_str = xml_str(info.get_long_description())
        description_node = self._xml.createElement('long-description')
        description = self._xml.createTextNode(desc_str)
        description_node.appendChild(description)
        message_node.appendChild(description_node)

        fix_str = xml_str(info.get_fix_guidance())
        fix_node = self._xml.createElement('fix-guidance')
        fix = self._xml.createTextNode(fix_str)
        fix_node.appendChild(fix)
        message_node.appendChild(fix_node)

        fix_effort_str = xml_str(info.get_fix_effort())
        fix_node = self._xml.createElement('fix-effort')
        fix = self._xml.createTextNode(fix_effort_str)
        fix_node.appendChild(fix)
        message_node.appendChild(fix_node)

        if info.get_references():
            references_node = self._xml.createElement('references')

            for ref in info.get_references():
                ref_node = self._xml.createElement('reference')
                ref_node.setAttribute('title', xml_str(ref.title))
                ref_node.setAttribute('url', xml_str(ref.url))
                references_node.appendChild(ref_node)

            message_node.appendChild(references_node)

    def _write_http_details_to_xml(self, message_node, info):
        """
        If there are HTTP requests and responses, then we should write
        them to the XML

        :param message_node: The xml node
        :param info: The Info() instance with the vuln information
        :return: None
        """
        if not info.get_id():
            return

        # HistoryItem to get requests/responses
        req_history = HistoryItem()

        message_node.setAttribute('id', str(info.get_id()))

        # Wrap all transactions in a http-transactions node
        transaction_set = self._xml.createElement('http-transactions')
        message_node.appendChild(transaction_set)

        for request_id in info.get_id():
            #
            # Get the node from the cache
            #
            xml_node = self._get_xml_node_from_cache(request_id)
            if xml_node is not None:
                return xml_node

            #
            # The node was not in the cache, we need to query the DB and create
            # it from scratch
            #
            try:
                # This DB query should be really fast, since the request ID is
                # the PK for the request/response database.
                #
                # Note that for each call to flush we will read() the same request
                # id over and over. The solution to this would be to cache this call
                # and only perform the query once.
                details = req_history.read(request_id)
            except DBException:
                msg = 'Failed to retrieve request with id %s from DB.'
                print(msg % request_id)
                continue

            # Wrap the entire http transaction in a single block
            action_set = self._xml.createElement('http-transaction')
            action_set.setAttribute('id', str(request_id))
            transaction_set.appendChild(action_set)

            request_node = self._xml.createElement('http-request')
            self.report_http_action(request_node, details.request)
            action_set.appendChild(request_node)

            response_node = self._xml.createElement('http-response')
            self.report_http_action(response_node, details.response)
            action_set.appendChild(response_node)

            # Save to the cache
            self._save_xml_node_to_cache(request_id, action_set)

    def _get_xml_node_from_cache(self, request_id):
        """
        Get the xml node from the cache. None is returned if the info
        is not in the cache.

        :param request_id: The HTTP request id
        :return: The DOM Element (from xml.dom.minidom)
        """
        cached_node_str = self._xml_node_cache.get(request_id, None)

        if cached_node_str is None:
            return None

        xml_node = xml.dom.minidom.parseString(cached_node_str).childNodes[0]
        return xml_node

    def _save_xml_node_to_cache(self, request_id, xml_node):
        """
        Save a node to the cache

        :param request_id: The HTTP request id
        :param xml_node: The xml_node representing the http traffic
        :return: None
        """
        node_str = xml_node.toxml(encoding=DEFAULT_ENCODING)
        self._xml_node_cache[request_id] = node_str

    def _get_finding_xml_node(self, info):
        """
        Get the xml node representing the info

        :param info: The finding
        :return: The xml node
        """
        xml_node = self._xml.createElement('vulnerability')

        xml_node.setAttribute('severity', xml_str(info.get_severity()))
        xml_node.setAttribute('method', xml_str(info.get_method()))
        xml_node.setAttribute('url', xml_str(info.get_url()))
        xml_node.setAttribute('var', xml_str(info.get_token_name()))
        xml_node.setAttribute('name', xml_str(info.get_name()))
        xml_node.setAttribute('plugin', xml_str(info.get_plugin_name()))

        # Wrap description in a <description> element and put it above the
        # request/response elements
        desc_str = xml_str(info.get_desc(with_id=False))
        description_node = self._xml.createElement('description')
        description = self._xml.createTextNode(desc_str)
        description_node.appendChild(description)
        xml_node.appendChild(description_node)

        self._write_vulndb_details_to_xml(xml_node, info)
        self._write_http_details_to_xml(xml_node, info)

        return xml_node

    def _write_findings_to_xml(self):
        """
        Write all the findings to the XML file
        :return: None, we write the data to the XML
        """
        for info in kb.kb.get_all_findings():
            xml_node = self._get_finding_xml_node(info)
            self._top_elem.appendChild(xml_node)

    def _log_enabled_plugins_to_xml(self):
        """
        The previous versions of this plugin kept a lot of data in memory, using
        a xml.dom.minidom.Document. Now we keep the data in raw format in memory and
        just open the XML when we're writing to it.

        :return: None
        """
        self._scan_info = self._xml.createElement('scan-info')

        # Add the user configured targets to scan-info
        str_targets = ','.join([xml_str(t.url_string) for t in cf.cf.get('targets')])
        self._scan_info.setAttribute('target', str_targets)

        # Add enabled plugins and their configuration to scan-info
        for plugin_type in self._plugins_dict:
            self._build_plugin_scaninfo(plugin_type,
                                        self._plugins_dict[plugin_type],
                                        self._options_dict[plugin_type])

        # Add scan-info to the report
        self._top_elem.appendChild(self._scan_info)

    def _build_plugin_scaninfo(self, group_name, plugin_list, options_dict):
        """
        This method builds the xml structure for the plugins and their
        configuration
        """
        node = self._xml.createElement(xml_str(group_name))
        for plugin_name in plugin_list:
            plugin_node = self._xml.createElement('plugin')
            plugin_node.setAttribute('name', xml_str(plugin_name))

            if plugin_name in options_dict:
                for plugin_option in options_dict[plugin_name]:
                    config_node = self._xml.createElement('config')
                    config_node.setAttribute('parameter',
                                             xml_str(plugin_option.get_name()))
                    config_node.setAttribute('value',
                                             xml_str(plugin_option.get_value()))
                    plugin_node.appendChild(config_node)

            node.appendChild(plugin_node)

        self._scan_info.appendChild(node)

    def report_http_action(self, parent_node, action):
        """
        Write out the request/response in a more parseable XML format will
        factor anything with a content-type not prefixed with a text/ in a
        CDATA.

        parent - the parent node (eg http-request/http-response)
        action - either a details.request or details.response
        """
        headers, body = self.handle_headers(parent_node, action)

        if body:
            self.handle_body(parent_node, headers, body)

    def handle_headers(self, parent_node, action):
        if isinstance(action, HTTPRequest):
            headers = action.get_headers()
            body = action.get_data() or ''
            status = xml_str(action.get_request_line())
        else:
            headers = action.headers
            body = action.body or ''
            status = xml_str(action.get_status_line())

        # Put out the status as an element
        action_status_node = self._xml.createElement('status')
        # strip is to remove the extraneous newline
        action_status = self._xml.createTextNode(status.strip())
        action_status_node.appendChild(action_status)
        parent_node.appendChild(action_status_node)

        # Put out the headers as XML entity
        action_headers_node = self._xml.createElement('headers')
        for header, header_content in headers.iteritems():
            header_detail = self._xml.createElement('header')
            header_detail.setAttribute('content', xml_str(header_content))
            header_detail.setAttribute('field', xml_str(header))
            action_headers_node.appendChild(header_detail)

        parent_node.appendChild(action_headers_node)

        return headers, body

    def handle_body(self, parent_node, headers, body):
        """
        Create the XML tags that hold the http request or response body
        """
        action_body_node = self._xml.createElement('body')
        action_body_node.setAttribute('content-encoding', 'text')

        # https://github.com/andresriancho/w3af/issues/264 is fixed by encoding
        # the ']]>', which in some cases would end up in a CDATA section and
        # break it, using base64 encoding
        if INVALID_XML.search(body) or ']]>' in body:
            # irrespective of the mimetype; if the NULL char is present; then
            # base64.encode it
            encoded = base64.encodestring(xml_str(body, replace_invalid=False))
            action_body_content = self._xml.createTextNode(encoded)
            action_body_node.setAttribute('content-encoding', 'base64')

        else:
            # try and extract the Content-Type header
            content_type, _ = headers.iget('Content-Type', '')

            try:
                # if we know the Content-Type (ie it's in the headers)
                mime_type, sub_type = content_type.split('/', 1)
            except ValueError:
                # not strictly valid mime-type, it doesn't respect the usual
                # foo/bar format. Play it safe with the content by forcing it
                # to be written in base64 encoded form
                mime_type = 'application'
                sub_type = 'octet-stream'

            if mime_type == 'text':
                # There shouldn't be any invalid chars, so for perf we just send
                # false and avoid a RE sub call to the body
                encoded_body = xml_str(body, replace_invalid=False)
                action_body_content = self._xml.createTextNode(encoded_body)

            elif mime_type == 'application' and sub_type in NON_BIN:
                # Textual type application, eg json, javascript
                # which for readability we'd rather not base64.encode
                #
                # There shouldn't be any invalid chars, so for perf we just send
                # false and avoid a RE sub call to the body
                encoded_body = xml_str(body, replace_invalid=False)
                action_body_content = self._xml.createCDATASection(encoded_body)

            else:
                # either known (image, audio, video) or unknown binary format
                # Write it as base64encoded text
                encoded = base64.encodestring(xml_str(body, replace_invalid=False))
                action_body_content = self._xml.createTextNode(encoded)
                action_body_node.setAttribute('content-encoding', 'base64')

        action_body_node.appendChild(action_body_content)
        parent_node.appendChild(action_body_node)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin creates an XML file containing all of w3af's findings.

        One configurable parameter exists:
            - output_file

        When using the contents of the XML file it's important to notice that
        the long-description and fix-guidance tags contain text in markdown
        format.

        The generated XML file validates against the report.xsd file which is
        distributed with the plugin.
        """
