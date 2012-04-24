'''
xmlFile.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
from functools import partial
import base64
import os
import time
import xml.dom.minidom

from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
from core.controllers.misc import get_w3af_version
from core.controllers.misc.encoding import smart_str
from core.controllers.w3afException import w3afException
from core.data.db.history import HistoryItem
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.request.fuzzableRequest import fuzzableRequest
import core.data.constants.severity as severity
import core.data.kb.config as cf
import core.data.kb.knowledgeBase as kb

# Override builtin 'str' function in order to avoid encoding
# errors while generating objects' utf8 bytestring representations.
# Note that this 'str' re-definition only will be available within
# this module's scope.
str = partial(smart_str, encoding='utf8', errors='xmlcharrefreplace')


class xmlFile(baseOutputPlugin):
    '''
    Print all messages to a xml file.
    
    @author: Kevin Denver ( muffysw@hotmail.com )
    '''
    def __init__(self):
        baseOutputPlugin.__init__(self)
        
        # These attributes hold the file pointers
        self._file = None
        
        # User configured parameters
        self._file_name = 'report.xml'
        self._timeFormat = '%a %b %d %H:%M:%S %Y'
        self._longTimestampString = str(time.strftime(self._timeFormat, time.localtime()))
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
        version_data = self._xmldoc.createTextNode(str(get_w3af_version.get_w3af_version()))
        version_element.appendChild(version_data)
        self._topElement.appendChild(version_element)
        
        self._scanInfo = self._xmldoc.createElement("scaninfo")
              
        # HistoryItem to get requests/responses
        self._history = HistoryItem()

                                
    def _init( self ):
        try:
            self._file = open(self._file_name, "w")
        except IOError, io:
            msg = 'Can\'t open report file "' + os.path.abspath(self._file_name) + '" for writing'
            msg += ': "' + io.strerror + '".'
            raise w3afException( msg )
        except Exception, e:
            msg = 'Cant open report file ' + self._file_name + ' for output.'
            msg += ' Exception: "' + str(e) + '".'
            raise w3afException( msg )

    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        '''
        pass
        
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        '''
        pass 
    
    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        messageNode = self._xmldoc.createElement("error")
        messageNode.setAttribute("caller", str(self.getCaller()))
        description = self._xmldoc.createTextNode(message)
        messageNode.appendChild(description)
        
        self._errorXML.append(messageNode)

    def vulnerability(self, message , newLine=True, severity=severity.MEDIUM ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        pass 
    
    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        pass
        
    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self._file_name = OptionList['fileName'].getValue()
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'File name where this plugin will write to'
        o1 = option('fileName', self._file_name, d1, 'string')

        ol = optionList()
        ol.add(o1)

        return ol

    def logHttp( self, request, response):
        '''
        log the http req / res to file.
        @parameter request: A fuzzable request object
        @parameter response: A httpResponse object
        '''
        pass
    
    def _buildPluginScanInfo(self, groupName, pluginList, optionsDict):
        '''
        This method builds the xml structure for the plugins
        and their configuration
        '''
        node = self._xmldoc.createElement(str(groupName))
        for pluginName in pluginList:
            pluginNode = self._xmldoc.createElement("plugin")
            pluginNode.setAttribute("name", str(pluginName))

            if optionsDict.has_key(pluginName):
                for plugin_option in optionsDict[pluginName]:
                    configNode = self._xmldoc.createElement("config")
                    configNode.setAttribute("parameter", str(plugin_option.getName()))
                    configNode.setAttribute("value", str(plugin_option.getValue()))
                    pluginNode.appendChild(configNode)
            node.appendChild(pluginNode)  
        self._scanInfo.appendChild(node)
        
    def logEnabledPlugins(self, pluginsDict, optionsDict):
        '''
        This method is called from the output manager object. This method should take an action
        for the enabled plugins and their configuration. Usually, write the info to a file or print
        it somewhere.
        
        @parameter pluginsDict: A dict with all the plugin types and the enabled plugins for that
                                               type of plugin.
        @parameter optionsDict: A dict with the options for every plugin.
        '''
        # Add the user configured targets to scaninfo
        strTargets = ''
        for url in cf.cf.getData('targets'):
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
        Write out the request/response in a more parseable XML format
         will factor anything with a content-type not prefixed with a text/ in a CDATA
        parent - the parent node (eg httprequest/httpresponse)
        action - either a details.request or details.response
        """
        NON_BIN = ['atom+xml', 'ecmascript', 'EDI-X12', 'EDIFACT', 'json',
                   'javascript', 'rss+xml', 'soap+xml', 'font-woff', 'xhtml+xml', 'xml-dtd',
                   'xop+xml']
        #escape_nulls = lambda str: str.replace('\0', 'NULL')
        if isinstance(action, fuzzableRequest):
            headers = action.getHeaders()
            body = str(action.getData() or '')
            status = action.getRequestLine()
        else:
            headers = action.headers
            body = str(action.body or '')
            status = action.getStatusLine()

        # Put out the status as an element
        actionStatusNode = self._xmldoc.createElement("status")
        # strip is to try and remove the extraneous newline
        actionStatus = self._xmldoc.createTextNode(status.strip())
        actionStatusNode.appendChild(actionStatus)
        parentNode.appendChild(actionStatusNode)

        # Put out the headers as XML entity
        actionHeaderNode = self._xmldoc.createElement("headers")
        for (header, header_content) in headers.iteritems():
            headerdetail = self._xmldoc.createElement("header")
            headerdetail.setAttribute("field", header)
            headerdetail.setAttribute("content", header_content)
            actionHeaderNode.appendChild(headerdetail)
        parentNode.appendChild(actionHeaderNode)
        # if the body is defined, put it out
        if body:
            actionBodyNode = self._xmldoc.createElement("body")
            actionBodyNode.setAttribute('content-encoding', 'text')
            if "\0" in body:
                # irrespective of the mimetype; if the NULL char is present; then base64.encode it
                actionBodyContent = self._xmldoc.createTextNode(base64.encodestring(body))
                actionBodyNode.setAttribute('content-encoding', 'base64')
            else:
                # try and extract the Content-Type header
                content_type = headers.get('Content-Type', "")
                try:
                    # if we know the Content-Type (ie it's in the headers)
                    (mime_type, sub_type) = content_type.split('/')
                    if mime_type in ['image', 'audio', 'video']:
                        # if one of image/, audio/, video/ put out base64encoded text
                        actionBodyContent = self._xmldoc.createTextNode(base64.encodestring(body))
                        actionBodyNode.setAttribute('content-encoding', 'base64')
                    elif mime_type == 'application':
                        if sub_type in NON_BIN:
                            # Textual type application, eg json, javascript which for readability we'd
                            # rather not base64.encode
                            actionBodyContent = self._xmldoc.createCDATASection(body)
                        else:
                            # either known or unknown binary format
                            actionBodyContent = self._xmldoc.createTextNode(base64.encodestring(body))
                            actionBodyNode.setAttribute('content-encoding', 'base64')
                    else:
                        actionBodyContent = self._xmldoc.createTextNode(body)
                except ValueError:
                    # not strictly valid mime-type, play it safe with the content
                    actionBodyContent = self._xmldoc.createCDATASection(body)
            actionBodyNode.appendChild(actionBodyContent)
            parentNode.appendChild(actionBodyNode)
    
    def end(self):
        '''
        This method is called when the scan has finished.
        '''
        # TODO: Aug 31 2011, Is there improvement for this? We are
        # removing null characters from the xml doc. Would this be a
        # significant loss of data for any scenario?
        #escape_nulls = lambda str: str.replace('\0', 'NULL')
        
        # Add the vulnerability results
        vulns = kb.kb.getAllVulns()
        for i in vulns:
            messageNode = self._xmldoc.createElement("vulnerability")
            messageNode.setAttribute("severity", str(i.getSeverity()))
            messageNode.setAttribute("method", str(i.getMethod()))
            messageNode.setAttribute("url", str(i.getURL()))
            messageNode.setAttribute("var", str(i.getVar()))
            messageNode.setAttribute("name", str(i.getName()))
            messageNode.setAttribute("plugin", str(i.getPluginName()))
            # Wrap description in a <description> element and put it above the request/response elements
            descriptionNode = self._xmldoc.createElement('description')
            description = self._xmldoc.createTextNode(i.getDesc())
            descriptionNode.appendChild(description)
            messageNode.appendChild(descriptionNode)
            if i.getId():
                messageNode.setAttribute("id", str(i.getId()))
                # Wrap all transactions in a http-transactions node
                transaction_set = self._xmldoc.createElement('http-transactions')
                messageNode.appendChild(transaction_set)
                for requestid in i.getId():
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
        infos = kb.kb.getAllInfos()
        for i in infos:
            messageNode = self._xmldoc.createElement("information")
            messageNode.setAttribute("url", str(i.getURL()))
            messageNode.setAttribute("name", str(i.getName()))
            messageNode.setAttribute("plugin", str(i.getPluginName()))
            # Wrap the description in a description element and put it above the request/response details
            descriptionNode = self._xmldoc.createElement('description')
            description = self._xmldoc.createTextNode(i.getDesc())
            descriptionNode.appendChild(description)
            messageNode.appendChild(descriptionNode)
            if i.getId():
                messageNode.setAttribute("id", str(i.getId()))
                # Wrap all transactions in a http-transactions node
                transaction_set = self._xmldoc.createElement('http-transactions')
                messageNode.appendChild(transaction_set)
                for requestid in i.getId():
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
            self._xmldoc.writexml(self._file, addindent=" "*4,
                                  newl="\n", encoding="UTF-8")  
            self._file.flush()
        finally:
            self._file.close()
              
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to an XML report file.
        
        One configurable parameter exists:
            - fileName
        '''
