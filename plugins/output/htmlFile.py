'''
htmlFile.py

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
import core.data.constants.severity as severity
import core.data.kb.config as cf

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import sys, os
import cgi 
import codecs

TITLE = 'w3af  -  Web Attack and Audit Framework - Vulnerability Report'

class htmlFile(baseOutputPlugin):
    '''
    Print all messages to a HTML file.
    
    @author: Juan Pablo Perez Etchegoyen ( jppereze@cybsec.com )
    '''
    def __init__(self):
        baseOutputPlugin.__init__(self)
        
        # Internal variables
        self._initialized = False
        self._aditional_info = ''
        self._style_filename = 'plugins' + os.path.sep + 'output' + os.path.sep
        self._style_filename += 'htmlFile' + os.path.sep +'style.css'        
        
        # These attributes hold the file pointers
        self._file = None
        
        # User configured parameters
        self._report_debug = False
        self._file_name = 'report.html'
    
    def _init( self ):
        self._initialized = True
        try:
            #self._file = codecs.open( self._file_name, "w", "utf-8", 'replace' )            
            self._file = open( self._file_name, "w" )
        except Exception, e:
            msg = 'Cant open report file ' + self._file_name + ' for output.'
            msg += ' Exception: "' + str(e) + '".'
            raise w3afException( msg )
        
        try:
            styleFile = open( self._style_filename, "r" )
        except:
            raise w3afException('Cant open style file ' + self._style_filename + '.')
        else:
            html = '<HTML>\n<HEAD>\n<TITLE>\n' +  cgi.escape ( TITLE ) + ' </TITLE>\n<meta'
            html += ' http-equiv="Content-Type" content="text/html; charset=iso-8859-1">\n'
            html += '<STYLE TYPE="text/css">\n<!--\n'
            self._write_to_file( html )
            self._write_to_file( styleFile.read() )
            self._write_to_file('//-->\n</STYLE>\n</HEAD>\n<BODY BGCOLOR=white>\n')
            styleFile.close()

    def _write_to_file( self, msg ):
        try:
            self._file.write( msg )
        except Exception, e:
            print 'An exception was raised while trying to write to the output file:', e
            sys.exit(1)
        
    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        '''
        if not self._initialized:
            self._init()
            
        if self._report_debug:
            toPrint = unicode ( self._cleanString(message) )
            self._aditional_info += '<tr>\n<td class=content>debug: ' + cgi.escape ( toPrint )
            self._aditional_info += ' \n</td></tr>\n'
    
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
        if not self._initialized:
            self._init()
        
        toPrint = unicode ( self._cleanString(message) )
        self._aditional_info += '<tr>\n<td class=content>error: ' + cgi.escape ( toPrint )
        self._aditional_info += ' \n</td></tr>\n'

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
        if not self._initialized:
            self._init()
        toPrint = unicode ( self._cleanString(message) )
        self._aditional_info += '<tr>\n<td class=content>console: ' + cgi.escape ( toPrint )
        self._aditional_info += ' \n</td></tr>\n'
    
    def logEnabledPlugins(self,  enabledPluginsDict,  pluginOptionsDict):
        '''
        This method is called from the output managerobject. 
        This method should take an action for the enabled plugins 
        and their configuration.
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
        self._report_debug = OptionList['reportDebug'].getValue()
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'File name where this plugin will write to'
        o1 = option('fileName', self._file_name, d1, 'string')
        
        d3 = 'True if debug information will be appended to the report.'
        o3 = option('reportDebug', self._report_debug, d3, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o3)
        return ol

    def logHttp( self, request, response):
        '''
        Do nothing.
        '''
        pass

    def end (self ):
        '''
        This method is called when the scan has finished.
        '''
        # Just in case...
        if not self._initialized:
            self._init()
            
        #
        # Write the configuration table!
        #
        self._write_to_file(
            '''<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="30%">
                <tbody> <tr><td>
                <table cellpadding=2 cellspacing=1 border=0 width="100%">
                <td class=title colspan=3>w3af target URL's</td>
                </tr>
                <tr>
                    <td class=sub width="100%">URL</td>
                </tr>''')       

        # Writes the targets to the HTML
        for i in cf.cf.getData('targets'):
            self._write_to_file('''<tr><td class=default width="100%">''')
            self._write_to_file( cgi.escape( i ) + '<br/>\n')
            self._write_to_file('</td></tr>')

        self._write_to_file('</td></tr></tbody></table></td></tr></tbody></table><br>')

    
        #
        # Write info and vulns
        #
        self._write_to_file(
            '''<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="75%">
                <tbody> <tr><td>
                <table cellpadding=2 cellspacing=1 border=0 width="100%">
                <td class=title colspan=3>Security Issues and Fixes</td>
                </tr>
                <tr>
                    <td class=sub width="10%">Type</td>
                    <td class=sub width="10%">Port</td>
                    <td class=sub width="80%">Issue </td>
                </tr>''')       

        # Writes the vulnerability results Table
        Vulns = kb.kb.getAllVulns()
        for i in Vulns:
            self._write_to_file(
                '''<tr>
                <td valign=top class=default width="10%"><font color=red>Vulnerability</td>
                <td valign=top class=default width="10%">tcp/80</td>
                <td class=default width="80%">'''
                )

            desc = cgi.escape( i.getDesc() ) + '<br/><br/><b>URL :</b> '
            desc += cgi.escape (i.getURL()) + '<br>\n'
            self._write_to_file( desc )

            if i.getSeverity() !=  None:
                self._write_to_file('Severity : ' + cgi.escape( i.getSeverity() ) +'<br> \n')
            self._write_to_file('</td></tr>')

        # Writes the Information results Table
        Infos = kb.kb.getAllInfos()     
        for i in Infos:
            self._write_to_file(
                '''<tr>
                    <td valign=top class=default width="10%">Information</td>
                    <td valign=top class=default width="10%">tcp/80</td>
                    <td class=default width="80%">'''
                )

            desc = cgi.escape( i.getDesc() ) + '<br>\n' + '<br/><b>URL :</b> '
            desc += cgi.escape (i.getURL()) + '<br> \n </td></tr>'
            self._write_to_file( desc )

        self._write_to_file('</td></tr></tbody></table></td></tr></tbody></table><br>')
        self._write_to_file(
            '''<table bgcolor="#a1a1a1" border=0 cellpadding=0 cellspacing=0 width="95%">
                <tbody>
                <tr><td><table border=0 cellpadding=2 cellspacing=1 width="100%">
                <tbody>
                <tr>
                <td class=title>w3af  Debug Information </td></tr>'''
            )
        self._write_to_file( self._aditional_info )
        self._write_to_file('</tbody></table></td></tr></tbody></table><br>')

        # Finish the report 
        self._write_to_file('</BODY>'+ '\n' + '</HTML>'+ '\n')
        
        # Close the file.
        if self._file != None:
            self._file.close()
            
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to an HTML report file.
        
        Four configurable parameters exist:
            - fileName
            - reportDebug

        If you want to write every HTTP request/response to a text file, you should use the
        textFile plugin.
        '''
