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
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

# severity constants for vuln messages
import core.data.constants.severity as severity

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
        self._aditionalInfo = ''
        self._styleFilename = 'plugins' + os.path.sep + 'output' + os.path.sep + 'htmlFile' + os.path.sep +'style.css'        
        
        # These attributes hold the file pointers
        self._file = None
        self._http = None
        
        # User configured parameters
        self._reportDebug = False
        self._fileName = 'report.html'
        self._httpFileName = 'output-http.txt'
    
    def _init( self ):
        self._initialized = True
        try:
            #self._file = codecs.open( self._fileName, "w", "utf-8", 'replace' )            
            self._file = open( self._fileName, "w" )
        except Exception, e:
            raise w3afException('Cant open report file ' + self._httpFileName + ' for output. Exception: ' + str(e) )
        
        try:
            # Images aren't ascii, so this file that logs every request/response, will be binary
            #self._http = codecs.open( self._httpFileName, "wb", "utf-8", 'replace' )
            self._http = open( self._httpFileName, "wb" )
        except Exception, e:
            raise w3afException('Cant open file ' + self._httpFileName + ' for output. Exception: ' + str(e) )
        
        try:
            styleFile = open( self._styleFilename, "r" )
        except:
            raise w3afException('Cant open style file ' + self._styleFilename + '.')
        else:
            self._writeToFile('<HTML>' + '\n' + '<HEAD>' + '\n' + '<TITLE>' + '\n' +  cgi.escape ( TITLE ) + ' </TITLE>' + '\n' + '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">' + '\n' + '<STYLE TYPE="text/css">' + '\n' + '<!-- ' + '\n' )
            self._writeToFile( styleFile.read() )
            self._writeToFile('//--> ' + '\n' + '</STYLE>' + '\n' + '</HEAD>' + '\n' + '<BODY BGCOLOR=white> ' + '\n')
            styleFile.close()

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
            toPrint = unicode ( self._cleanString(message) )
            self._aditionalInfo+= '<tr>\n<td class=content>debug: ' + cgi.escape ( toPrint ) + ' \n</td></tr>\n'
    
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
        self._aditionalInfo+= '<tr>\n<td class=content>error: ' + cgi.escape ( toPrint ) + ' \n</td></tr>\n'

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
        self._aditionalInfo+= '<tr>\n<td class=content>console: ' + cgi.escape ( toPrint ) + ' \n</td></tr>\n'
        
    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self._fileName = OptionList['fileName'].getValue()
        self._httpFileName = OptionList['httpFileName'].getValue()
        self._reportDebug = OptionList['reportDebug'].getValue()
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'File name where this plugin will write to'
        o1 = option('fileName', self._fileName, d1, 'string')
        
        d2 = 'File name where this plugin will write HTTP requests and responses'
        o2 = option('httpFileName', self._httpFileName, d2, 'string')
        
        d3 = 'True if debug information will be appended to the report.'
        o3 = option('reportDebug', self._reportDebug, d3, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        return ol

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
        '''
        This method is called when the scan has finished.
        '''
        # Just in case...
        if not self._initialized:
            self._init()
            
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
        # Finish the report 
        self._writeToFile('</BODY>'+ '\n' + '</HTML>'+ '\n')
        
        # Close the files.
        if self._file != None:
            self._file.close()
        
        if self._http != None:
            self._http.close()        
    
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
        '''
