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
import core.data.kb.config as cf
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
        self._filename = 'report.html'
        self._styleFilename = 'plugins' + os.path.sep + 'output' + os.path.sep + 'htmlFile' + os.path.sep +'style.css'
        self._httpFilename = 'output-http.txt'
        self._flushCounter = 0
        self._flushNumber = 10
        self._initialized = False
        self._aditionalInfo = ''
        self._file = None
        
        self._reportDebug = False
        
    
    def _init( self ):
        self._initialized = True
        try:
            self._file = codecs.open( self._filename, "w", "utf-8", 'replace' )            
        except Exception, e:
            raise w3afException('Cant open report file ' + self._httpFilename + ' for output. Exception: ' + str(e) )
            self._error = True
        
        try:
            # Images aren't ascii, so this file that logs every request/response, will be binary
            self._http = file( self._httpFilename, "wb" )
        except Exception, e:
            raise w3afException('Cant open file ' + self._httpFilename + ' for output. Exception: ' + str(e) )
            self._error = True      
        try:
            self._style = open( self._styleFilename, "r" )
        except:
            raise w3afException('Cant open style file ' + self._styleFilename + '.')
            self._error = True          
        self._writeToFile('<HTML>' + '\n' + '<HEAD>' + '\n' + '<TITLE>' + '\n' +  cgi.escape ( TITLE ) + ' </TITLE>' + '\n' + '<meta http-equiv="Content-Type" content="text/html; charset="iso-8859-1">' + '\n' + '<STYLE TYPE="text/css">' + '\n' + '<!-- ' + '\n' )
        self._writeToFile( self._style.read() )
        self._writeToFile('//--> ' + '\n' + '</STYLE>' + '\n' + '</HEAD>' + '\n' + '<BODY BGCOLOR=white> ' + '\n')              
    
    def __del__(self):
        if self._file != None:
            self._file.close()

    def _writeToFile( self, msg ):
        try:
            self._file.write( msg )
        except Exception, e:
            print 'An exception was raised while trying to write to the output file:', e
            sys.exit(1)
        
    def _writeToHTTPLog( self, msg ):
        try:
            self._http.write( msg )
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
            
        if self._reportDebug:
            toPrint = unicode ( message )
            self._aditionalInfo+= '<tr>\n<td class=content>debug: ' + cgi.escape ( toPrint ) + ' \n</td></tr>\n'
            self._flush()

    
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
        
        toPrint = unicode ( message )
        self._aditionalInfo+= '<tr>\n<td class=content>error: ' + cgi.escape ( toPrint ) + ' \n</td></tr>\n'
        self._flush()

    def vulnerability(self, message , newLine = True ):
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
        toPrint = unicode ( message )
        self._aditionalInfo+= '<tr>\n<td class=content>console: ' + cgi.escape ( toPrint ) + ' \n</td></tr>\n'
        self._flush()
        
    def _flush(self):
        '''
        textfile.flush is called every time a message is sent to this plugin.
        self._file.flush() is called every self._flushNumber
        '''
        if self._flushCounter % self._flushNumber == 0:
            self._file.flush()
            
    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptionsXML()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self.verbosity = OptionList['verbosity']            
        self._filename = OptionList['fileName']
        self._httpFilename = OptionList['httpFileName']     
        self._reportDebug = OptionList['reportDebug']
        
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/display.xsd
        
        This method MUST be implemented on every plugin. 
        
        @return: XML String
        @see: core/display.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="verbosity">\
                <default>'+str(self.verbosity)+'</default>\
                <desc>Verbosity level for this plugin.</desc>\
                <type>integer</type>\
            </Option>\
            <Option name="fileName">\
                <default>'+str(self._filename)+'</default>\
                <desc>File name where this plugin will write to</desc>\
                <type>string</type>\
            </Option>\
            <Option name="httpFileName">\
                <default>'+str(self._httpFilename)+'</default>\
                <desc>File name where this plugin will write HTTP requests and responses</desc>\
                <type>string</type>\
            </Option>\
            <Option name="reportDebug">\
                <default>'+str(self._reportDebug)+'</default>\
                <desc>True if debug information will be appended to the report.</desc>\
                <type>boolean</type>\
            </Option>\
        </OptionList>\
        '

    def logHttp( self, request, response):
        '''
        log the http req / res to file.
        @parameter request: A fuzzable request object
        @parameter response: A httpResponse object
        '''
        msg = '='*40  + 'Request ' + str(response.id) + '='*40 + '\n'
        self._writeToHTTPLog(  msg )
        self._writeToHTTPLog( request.dump() )
        msg2 = '\n' + '='*40  + 'Response ' + str(response.id) + '='*39 + '\n'
        self._writeToHTTPLog( msg2 )
        self._writeToHTTPLog( response.dump() )
        
        self._writeToHTTPLog( '\n' + '='*(len(msg)-1) + '\n')
        self._http.flush()

    def end (self ):
        #
        # Write the configuration table!
        #
        self._writeToFile('''<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="30%">
<tbody> <tr><td>
    <table cellpadding=2 cellspacing=1 border=0 width="100%">
    <td class=title colspan=3>w3af target URL's</td>
    </tr>
    <tr>
        <td class=sub width="100%">URL</td>
    </tr>''')       
        # Writes the targets to the HTML
        for i in cf.cf.getData('targets'):
            self._writeToFile('''<tr><td class=default width="100%">''')
            self._writeToFile( cgi.escape( i ) + '<br/>\n')
            self._writeToFile('</td></tr>')

        self._writeToFile('</td></tr></tbody></table></td></tr></tbody></table><br>')

    
        #
        # Write info and vulns
        #
        self._writeToFile('''<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="75%">
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
            self._writeToFile('''<tr>
        <td valign=top class=default width="10%"><font color=red>Vulnerability</td>
        <td valign=top class=default width="10%">tcp/80</td>
        <td class=default width="80%">''')
            self._writeToFile( cgi.escape( i.getDesc() ) + '<br/><br/><b>URL :</b> '+   cgi.escape (i.getURL()) + '<br>\n')
            if i.getSeverity() !=  None:
                self._writeToFile('Severity : ' + cgi.escape( i.getSeverity() ) +'<br> \n')
            self._writeToFile('</td></tr>')
        # Writes the Information results Table
        Infos = kb.kb.getAllInfos()     
        for i in Infos:
            self._writeToFile('''<tr>
        <td valign=top class=default width="10%">Information</td>
        <td valign=top class=default width="10%">tcp/80</td>
        <td class=default width="80%">''')
            self._writeToFile( cgi.escape( i.getDesc() ) + '<br>\n' + '<br/><b>URL :</b> '+ cgi.escape (i.getURL()) + '<br> \n </td></tr>')
        self._writeToFile('</td></tr></tbody></table></td></tr></tbody></table><br>')
        self._writeToFile('''<table bgcolor="#a1a1a1" border=0 cellpadding=0 cellspacing=0 width="95%">
<tbody>
    <tr><td><table border=0 cellpadding=2 cellspacing=1 width="100%">
    <tbody>
    <tr>
    <td class=title>w3af  Debug Information </td></tr>''')
        self._writeToFile( self._aditionalInfo )
        self._writeToFile('</tbody></table></td></tr></tbody></table><br>')
        # Finnish the report 
        self._writeToFile('</BODY>'+ '\n' + '</HTML>'+ '\n')        
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to an HTML report file.
        
        Four configurable parameters exist:
            - fileName
            - httpFileName
            - reportDebug
            - verbosity
            
        '''
