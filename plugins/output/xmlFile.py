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

from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
from core.controllers.w3afException import w3afException
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

# severity constants for vuln messages
import core.data.constants.severity as severity

# xml
import xml.dom.minidom

# time
import time
import os


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
        self._topElement.setAttribute("xmloutputversion", "1.00")
        self._scanInfo = self._xmldoc.createElement("scaninfo")
                                              
    def _init( self ):
        try:
            self._file = open( self._file_name, "w" )
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

    def end (self):
        '''
        This method is called when the scan has finished.
        '''
        # Add the vulnerability results
        vulns = kb.kb.getAllVulns()
        for i in vulns:
            messageNode = self._xmldoc.createElement("vulnerability")
            messageNode.setAttribute("severity", str(i.getSeverity()))
            messageNode.setAttribute("method", str(i.getMethod()))
            messageNode.setAttribute("url", str(i.getURL()))
            messageNode.setAttribute("var", str(i.getVar()))
            if i.getId():
                messageNode.setAttribute("id", str(i.getId()))
            messageNode.setAttribute("name", str(i.getName()))
            messageNode.setAttribute("plugin", str(i.getPluginName()))
            description = self._xmldoc.createTextNode(i.getDesc())
            messageNode.appendChild(description)
            self._topElement.appendChild(messageNode)
        
        # Add the information results
        infos = kb.kb.getAllInfos()
        for i in infos:
            messageNode = self._xmldoc.createElement("information")
            messageNode.setAttribute("url", str(i.getURL()))
            if i.getId():
                messageNode.setAttribute("id", str(i.getId()))
            messageNode.setAttribute("name", str(i.getName()))
            messageNode.setAttribute("plugin", str(i.getPluginName()))
            description = self._xmldoc.createTextNode(i.getDesc())
            messageNode.appendChild(description)
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
