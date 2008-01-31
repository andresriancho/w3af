'''
errorPages.py

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

import core.controllers.outputManager as om
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
from core.data.getResponseType import *
import re
import core.data.constants.severity as severity

class errorPages(baseGrepPlugin):
    '''
    Grep every page for error pages.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._alreadyReportedVersions = []
        self._compiledRegex = []

    def _getDescriptiveMessages( self ):
        mesg = []
        
        mesg.append('<H1>Error page exception</H1>')
        mesg.append('<span><H1>Server Error in ')
        mesg.append('<H3>Original Exception: </H3>')
        mesg.append('Server object error')
        mesg.append('invalid literal for int()')
        mesg.append('exceptions.ValueError')
        mesg.append('Microsoft VBScript runtime')
        mesg.append('<font face="Arial" size=2>Type mismatch: ')
        mesg.append('[an error occurred while processing this directive]')
        mesg.append('<HTML><HEAD><TITLE>Error Occurred While Processing Request</TITLE></HEAD><BODY><HR><H3>Error Occurred While Processing Request</H3><P>')
        
        # ASP error I found during a pentest, the ASP used a foxpro db, not a SQL injection
        mesg.append('<font face="Arial" size=2>error \'800a0005\'</font>')
        mesg.append('<h2> <i>Runtime Error</i> </h2></span>')
        
        # Struts
        mesg.append('] does not contain handler parameter named')
        
        # PHP
        mesg.append('<b>Warning</b>: ')
        mesg.append('No row with the given identifier')
        mesg.append("eval()'d code</b> on line <b>")

        # Java
        mesg.append('[java.lang.')
        mesg.append('class java.lang.')
        mesg.append('java.lang.NullPointerException')
        
        mesg.append('onclick="toggle(\'full exception chain stacktrace\')"')
        mesg.append('at org.apache.catalina')
        mesg.append('at org.apache.coyote.')
        mesg.append('at org.apache.tomcat.')
        mesg.append('at org.apache.jasper.')
        
        # http://www.programacion.net/asp/articulo/kbr_execute/
        mesg.append('Server.Execute Error')
        
        return mesg
        
    def _testResponse(self, request, response):
        
        if isTextOrHtml(response.getHeaders()):
            for msg in self._getDescriptiveMessages():
                if response.getBody().count( msg ) and response.getURL():
                    
                    i = info.info()
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.setSeverity(severity.LOW)
                    i.setName( 'Error page' )
                    i.setDesc( 'The URL : ' + response.getURL() + ' is a descriptive error page. Showing the error: ' + msg )
                    kb.kb.append( self , 'errorPage' , i )
                    
            # Now i'll check if I can get a version number from the error page
            # This is common in apache, tomcat, etc...
            if response.getCode() in range( 400,600 ):
                
                for server, errorRegex in self._getRegexTuples():
                    res = errorRegex.search( response.getBody() )
                    if res:
                        resStr = res.groups()[0]
                        if resStr not in self._alreadyReportedVersions:
                            # Save the info obj
                            i = info.info()
                            i.setURL( response.getURL() )
                            i.setId( response.id )
                            i.setName( 'Error page' )
                            i.setDesc( 'An error page sent this ' + server +' version: ' + resStr  )
                            kb.kb.append( self , 'server' , i )
                            # Save the string
                            kb.kb.append( self , 'server' , resStr )
                            self._alreadyReportedVersions.append( resStr )

    def _getRegexTuples( self ):
        '''
        @return: A list of tuples with ( serverName, regexError )
        '''
        if not self._compiledRegex:
            self._compiledRegex.append( ('Apache', re.compile('<address>(.*?)</address>') ) )
            self._compiledRegex.append( ('Apache Tomcat',re.compile('<HR size="1" noshade="noshade"><h3>(.*?)</h3></body>') ) )
            self._compiledRegex.append( ('IIS', re.compile('<a href="http://www.microsoft.com/ContentRedirect.asp\?prd=iis&sbp=&pver=(.*?)&pid=&ID') ) )
            # <b>Version Information:</b>&nbsp;Microsoft .NET Framework Version:1.1.4322.2300; ASP.NET Version:1.1.4322.2300
            self._compiledRegex.append( ('ASP .Net', re.compile('<b>Version Information:</b>&nbsp;(.*?)\n') ) )

        return self._compiledRegex
        
    def setOptions( self, OptionList ):
        pass
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'errorPages', 'errorPage' ), 'URL' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for error Pages.
        '''
