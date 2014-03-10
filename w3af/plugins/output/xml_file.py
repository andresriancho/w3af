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
import base64
import os
import time
import xml.dom.minidom

from functools import partial

import w3af.core.data.kb.config as cf
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.controllers.misc import get_w3af_version
from w3af.core.data.misc.encoding import smart_str
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.db.history import HistoryItem
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.url.HTTPRequest import HTTPRequest

# Override builtin 'str' function in order to avoid encoding
# errors while generating objects' utf8 bytestring representations.
# Note that this 'str' re-definition only will be available within
# this module's scope.
str = partial(smart_str, encoding='utf8', errors='xmlcharrefreplace')

NON_BIN = ('atom+xml', 'ecmascript', 'EDI-X12', 'EDIFACT', 'json',
           'javascript', 'rss+xml', 'soap+xml', 'font-woff',
           'xhtml+xml', 'xml-dtd', 'xop+xml')

class xml_file(OutputPlugin):
    """
    Print all messages to a xml file.

    :author: Kevin Denver ( muffysw@hotmail.com )
    """
    def __init__(self):
        OutputPlugin.__init__(self)

        # These attributes hold the file pointers
        self._file = None

        # User configured parameters
        self._file_name = '~/report.xml'
        self._timeFormat = '%a %b %d %H:%M:%S %Y'
        self._longTimestampString = str(
            time.strftime(self._timeFormat, time.localtime()))
        self._timestampString = str(int(time.time()))

        # List with additional xml elements
        self._errorXML = []

        # xml
        self._xmldoc = xml.dom.minidom.Document()
        self._topElement = self._xmldoc.createElement("w3afrun")
        self._topElement.setAttribute("start", self._timestampString)
        self._topElement.setAttribute("startstr", self._longTimestampString)
        self._topElement.setAttribute("xmloutputversion", "2.0")
        # Add in the version details
        version_element = self._xmldoc.createElement("w3af-version")
        version_data = self._xmldoc.createTextNode(
            str(get_w3af_version.get_w3af_version()))
        version_element.appendChild(version_data)
        self._topElement.appendChild(version_element)

        self._scanInfo = self._xmldoc.createElement("scaninfo")

        # HistoryItem to get requests/responses
        self._history = HistoryItem()

    def _init(self):
        self._file_name = os.path.expanduser(self._file_name)
        try:
            self._file = open(self._file_name, "w")
        except IOError, io:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            raise BaseFrameworkException(msg % (os.path.abspath(self._file_name),
                                       io.strerror))
        except Exception, e:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            raise BaseFrameworkException(msg % (os.path.abspath(self._file_name), e))

    def do_nothing(self, *args, **kwds):
        pass
    debug = information = vulnerability = console = log_http = do_nothing

    def error(self, message, new_line=True):
        """
        This method is called from the output object. The output object was called
        from a plugin or from the framework. This method should take an action
        for error messages.
        """
        messageNode = self._xmldoc.createElement("error")
        messageNode.setAttribute("caller", str(self.get_caller()))
        description = self._xmldoc.createTextNode(message)
        messageNode.appendChild(description)

        self._errorXML.append(messageNode)

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

        d = 'File name where this plugin will write to'
        o = opt_factory('output_file', self._file_name, d, OUTPUT_FILE)
        ol.add(o)

        return ol

    def _buildPluginScanInfo(self, groupName, pluginList, optionsDict):
        """
        This method builds the xml structure for the plugins
        and their configuration
        """
        node = self._xmldoc.createElement(str(groupName))
        for plugin_name in pluginList:
            pluginNode = self._xmldoc.createElement("plugin")
            pluginNode.setAttribute("name", str(plugin_name))

            if plugin_name in optionsDict:
                for plugin_option in optionsDict[plugin_name]:
                    configNode = self._xmldoc.createElement("config")
                    configNode.setAttribute(
                        "parameter", str(plugin_option.get_name()))
                    configNode.setAttribute(
                        "value", str(plugin_option.get_value()))
                    pluginNode.appendChild(configNode)
            node.appendChild(pluginNode)
        self._scanInfo.appendChild(node)

    def log_enabled_plugins(self, pluginsDict, optionsDict):
        """
        This method is called from the output manager object. This method should
        take an action for the enabled plugins and their configuration. Usually,
        write the info to a file or print it somewhere.

        :param pluginsDict: A dict with all the plugin types and the enabled
                                plugins for that type of plugin.
        :param optionsDict: A dict with the options for every plugin.
        """
        # Add the user configured targets to scaninfo
        strTargets = ''
        for url in cf.cf.get('targets'):
            strTargets += str(url) + ","
        self._scanInfo.setAttribute("target", strTargets[:-1])

        # Add enabled plugins and their configuration to scaninfo
        for plugin_type in pluginsDict:
            self._buildPluginScanInfo(plugin_type, pluginsDict[plugin_type],
                                      optionsDict[plugin_type])

        # Add scaninfo to the report
        self._topElement.appendChild(self._scanInfo)

    def report_http_action(self, parentNode, action):
        """
        Write out the request/response in a more parseable XML format will factor
        anything with a content-type not prefixed with a text/ in a CDATA.

        parent - the parent node (eg httprequest/httpresponse)
        action - either a details.request or details.response
        """
        headers, body = self.handle_headers(parentNode, action)
        
        if body:
            self.handle_body(parentNode, headers, body)

    def handle_headers(self, parentNode, action):
        #escape_nulls = lambda str: str.replace('\0', 'NULL')
        if isinstance(action, HTTPRequest):
            headers = action.get_headers()
            body = str(action.get_data() or '')
            status = action.get_request_line()
        else:
            headers = action.headers
            body = str(action.body or '')
            status = action.get_status_line()

        # Put out the status as an element
        actionStatusNode = self._xmldoc.createElement("status")
        # strip is to try and remove the extraneous newline
        actionStatus = self._xmldoc.createTextNode(status.strip())
        actionStatusNode.appendChild(actionStatus)
        parentNode.appendChild(actionStatusNode)

        # Put out the headers as XML entity
        actionHeadersNode = self._xmldoc.createElement("headers")
        for (header, header_content) in headers.iteritems():
            headerdetail = self._xmldoc.createElement("header")
            headerdetail.setAttribute("content", str(header_content))
            headerdetail.setAttribute("field", str(header))
            actionHeadersNode.appendChild(headerdetail)
        parentNode.appendChild(actionHeadersNode)

        return headers, body
    
    def handle_body(self, parentNode, headers, body):
        """
        Create the XML tags that hold the http request or response body
        """
        actionBodyNode = self._xmldoc.createElement("body")
        actionBodyNode.setAttribute('content-encoding', 'text')
        
        # https://github.com/andresriancho/w3af/issues/264 is fixed by encoding
        # the ']]>', which in some cases would end up in a CDATA section and
        # break it, using base64 encoding
        if '\0' in body or ']]>' in body:
            # irrespective of the mimetype; if the NULL char is present; then
            # base64.encode it
            encoded = base64.encodestring(body)
            actionBodyContent = self._xmldoc.createTextNode(encoded)
            actionBodyNode.setAttribute('content-encoding', 'base64')
        
        else:
            # try and extract the Content-Type header
            content_type, _ = headers.iget('Content-Type', "")
            
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
                actionBodyContent = self._xmldoc.createTextNode(body)
                
            elif mime_type == 'application' and sub_type in NON_BIN:
                # Textual type application, eg json, javascript
                # which for readability we'd rather not base64.encode
                actionBodyContent = self._xmldoc.createCDATASection(body)
                
            else:
                # either known (image, audio, video) or unknown binary format
                # Write it as base64encoded text
                encoded = base64.encodestring(body)
                actionBodyContent = self._xmldoc.createTextNode(encoded)
                actionBodyNode.setAttribute('content-encoding', 'base64')

        actionBodyNode.appendChild(actionBodyContent)
        parentNode.appendChild(actionBodyNode)

    def end(self):
        """
        This method is called when the scan has finished.
        """
        # TODO: Aug 31 2011, Is there improvement for this? We are
        # removing null characters from the xml doc. Would this be a
        # significant loss of data for any scenario?
        #escape_nulls = lambda str: str.replace('\0', 'NULL')

        # Add the vulnerability results
        vulns = kb.kb.get_all_vulns()
        for i in vulns:
            messageNode = self._xmldoc.createElement("vulnerability")
            messageNode.setAttribute("severity", str(i.get_severity()))
            messageNode.setAttribute("method", str(i.get_method()))
            messageNode.setAttribute("url", str(i.get_url()))
            messageNode.setAttribute("var", str(i.get_var()))
            messageNode.setAttribute("name", str(i.get_name()))
            messageNode.setAttribute("plugin", str(i.get_plugin_name()))
            # Wrap description in a <description> element and put it above the
            # request/response elements
            descriptionNode = self._xmldoc.createElement('description')
            description = self._xmldoc.createTextNode(i.get_desc())
            descriptionNode.appendChild(description)
            messageNode.appendChild(descriptionNode)
            if i.get_id():
                messageNode.setAttribute("id", str(i.get_id()))
                # Wrap all transactions in a http-transactions node
                transaction_set = self._xmldoc.createElement(
                    'http-transactions')
                messageNode.appendChild(transaction_set)
                for requestid in i.get_id():
                    details = self._history.read(requestid)
                    # Wrap the entire http transaction in a single block
                    actionset = self._xmldoc.createElement("http-transaction")
                    actionset.setAttribute("id", str(requestid))
                    transaction_set.appendChild(actionset)

                    requestNode = self._xmldoc.createElement("httprequest")
                    self.report_http_action(requestNode, details.request)
                    actionset.appendChild(requestNode)

                    responseNode = self._xmldoc.createElement("httpresponse")
                    self.report_http_action(responseNode, details.response)
                    actionset.appendChild(responseNode)

            self._topElement.appendChild(messageNode)

        # Add the information results
        infos = kb.kb.get_all_infos()
        for i in infos:
            messageNode = self._xmldoc.createElement("information")
            messageNode.setAttribute("url", str(i.get_url()))
            messageNode.setAttribute("name", str(i.get_name()))
            messageNode.setAttribute("plugin", str(i.get_plugin_name()))
            # Wrap the description in a description element and put it above
            # the request/response details
            descriptionNode = self._xmldoc.createElement('description')
            description = self._xmldoc.createTextNode(i.get_desc())
            descriptionNode.appendChild(description)
            messageNode.appendChild(descriptionNode)
            if i.get_id():
                messageNode.setAttribute("id", str(i.get_id()))
                # Wrap all transactions in a http-transactions node
                transaction_set = self._xmldoc.createElement(
                    'http-transactions')
                messageNode.appendChild(transaction_set)
                for requestid in i.get_id():
                    details = self._history.read(requestid)
                    # Wrap the entire http transaction in a single block
                    actionset = self._xmldoc.createElement("http-transaction")
                    actionset.setAttribute("id", str(requestid))
                    transaction_set.appendChild(actionset)
                    # create a node for the request content
                    requestNode = self._xmldoc.createElement("httprequest")
                    self.report_http_action(requestNode, details.request)
                    actionset.appendChild(requestNode)
                    # create a node for the response content
                    responseNode = self._xmldoc.createElement("httpresponse")
                    responseNode.setAttribute("id", str(requestid))
                    self.report_http_action(responseNode, details.response)
                    actionset.appendChild(responseNode)

            self._topElement.appendChild(messageNode)

        # Add additional information results
        for node in self._errorXML:
            self._topElement.appendChild(node)

        # Write xml report
        self._init()
        self._xmldoc.appendChild(self._topElement)

        try:
            self._xmldoc.writexml(self._file, addindent=" " * 4,
                                  newl="\n", encoding="UTF-8")
            self._file.flush()
        finally:
            self._file.close()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin writes the framework messages to an XML report file.

        One configurable parameter exists:
            - output_file
        """
