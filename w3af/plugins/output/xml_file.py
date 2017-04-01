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
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.url.HTTPRequest import HTTPRequest


NON_BIN = ('atom+xml', 'ecmascript', 'EDI-X12', 'EDIFACT', 'json',
           'javascript', 'rss+xml', 'soap+xml', 'font-woff',
           'xhtml+xml', 'xml-dtd', 'xop+xml')

TIME_FORMAT = '%a %b %d %H:%M:%S %Y'

# https://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python
INVALID_XML = u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\u10000-\u10FFFF]+'


def xml_str(s):
    """
    Avoid encoding errors while generating objects' utf8 byte-string
    representations.

    Should fix issues similar to:
    https://github.com/andresriancho/w3af/issues/12924

    :param s: The input string/unicode
    :return: A string ready to be sent to the XML file
    """
    encoded_str = smart_str(s, encoding='utf8', errors='xmlcharrefreplace')
    encoded_str = re.sub(INVALID_XML, '?', encoded_str)
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

    def flush(self):
        """
        Write the XML to the output file
        :return: None
        """
        # Start from a clean state, just in case.
        self._empty_xml_root()

        self._create_root_xml_elems()
        self._log_enabled_plugins_to_xml()
        self._write_findings_to_xml()
        self._write_errors_to_xml()
        self._write_xml_to_file()

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
                               encoding='UTF-8')
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

    def _write_findings_to_xml(self):
        """
        Write all the findings to the XML file
        :return: None, we write the data to the XML
        """
        # HistoryItem to get requests/responses
        req_history = HistoryItem()

        for i in kb.kb.get_all_findings():
            message_node = self._xml.createElement('vulnerability')

            message_node.setAttribute('severity', xml_str(i.get_severity()))
            message_node.setAttribute('method', xml_str(i.get_method()))
            message_node.setAttribute('url', xml_str(i.get_url()))
            message_node.setAttribute('var', xml_str(i.get_token_name()))
            message_node.setAttribute('name', xml_str(i.get_name()))
            message_node.setAttribute('plugin', xml_str(i.get_plugin_name()))

            # Wrap description in a <description> element and put it above the
            # request/response elements
            desc_str = xml_str(i.get_desc(with_id=False))
            description_node = self._xml.createElement('description')
            description = self._xml.createTextNode(desc_str)
            description_node.appendChild(description)
            message_node.appendChild(description_node)

            # If there is information from the vulndb, then we should write it
            if i.has_db_details():
                desc_str = xml_str(i.get_long_description())
                description_node = self._xml.createElement('long-description')
                description = self._xml.createTextNode(desc_str)
                description_node.appendChild(description)
                message_node.appendChild(description_node)

                fix_str = xml_str(i.get_fix_guidance())
                fix_node = self._xml.createElement('fix-guidance')
                fix = self._xml.createTextNode(fix_str)
                fix_node.appendChild(fix)
                message_node.appendChild(fix_node)

                fix_effort_str = xml_str(i.get_fix_effort())
                fix_node = self._xml.createElement('fix-effort')
                fix = self._xml.createTextNode(fix_effort_str)
                fix_node.appendChild(fix)
                message_node.appendChild(fix_node)

                if i.get_references():
                    references_node = self._xml.createElement('references')

                    for ref in i.get_references():
                        ref_node = self._xml.createElement('reference')
                        ref_node.setAttribute('title', xml_str(ref.title))
                        ref_node.setAttribute('url', xml_str(ref.url))
                        references_node.appendChild(ref_node)

                    message_node.appendChild(references_node)

            if i.get_id():
                message_node.setAttribute('id', str(i.get_id()))
                # Wrap all transactions in a http-transactions node
                transaction_set = self._xml.createElement('http-transactions')
                message_node.appendChild(transaction_set)

                for request_id in i.get_id():
                    try:
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

            self._top_elem.appendChild(message_node)

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
            body = xml_str(action.get_data() or '')
            status = xml_str(action.get_request_line())
        else:
            headers = action.headers
            body = xml_str(action.body or '')
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
        if '\0' in body or ']]>' in body:
            # irrespective of the mimetype; if the NULL char is present; then
            # base64.encode it
            encoded = base64.encodestring(body)
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
                action_body_content = self._xml.createTextNode(body)

            elif mime_type == 'application' and sub_type in NON_BIN:
                # Textual type application, eg json, javascript
                # which for readability we'd rather not base64.encode
                action_body_content = self._xml.createCDATASection(body)

            else:
                # either known (image, audio, video) or unknown binary format
                # Write it as base64encoded text
                encoded = base64.encodestring(body)
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
