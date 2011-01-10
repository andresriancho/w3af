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
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

import re


class errorPages(baseGrepPlugin):
    '''
    Grep every page for error pages.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._already_reported_versions = []
        self._compiled_regex = []

    def _get_error_strings( self ):
        '''
        @return: A list of strings that are present in different error pages.
        '''
        mesg = []
        
        mesg.append('<H1>Error page exception</H1>')
        # This signature fires up also in default 404 pages of aspx which generates 
        # a lot of noise, so ... disabling it
        #mesg.append('<span><H1>Server Error in ')
        mesg.append('<h2> <i>Runtime Error</i> </h2></span>')
        mesg.append('<h2> <i>Access is denied</i> </h2></span>')
        mesg.append('<H3>Original Exception: </H3>')
        mesg.append('Server object error')
        mesg.append('invalid literal for int()')
        mesg.append('exceptions.ValueError')
        
        mesg.append('<font face="Arial" size=2>Type mismatch: ')
        mesg.append('[an error occurred while processing this directive]')
        error_msg = '<HTML><HEAD><TITLE>Error Occurred While Processing Request</TITLE>'
        error_msg += '</HEAD><BODY><HR><H3>Error Occurred While Processing Request</H3><P>'
        mesg.append(error_msg)
        
        # VBScript
        mesg.append('<p>Microsoft VBScript runtime </font>')
        mesg.append("<font face=\"Arial\" size=2>error '800a000d'</font>")

        # nwwcgi errors
        mesg.append('<TITLE>nwwcgi Error')
        
        # ASP error I found during a pentest, the ASP used a foxpro db, not a SQL injection
        mesg.append('<font face="Arial" size=2>error \'800a0005\'</font>')
        mesg.append('<h2> <i>Runtime Error</i> </h2></span>')
        # Some error in ASP when using COM objects.
        mesg.append('Operation is not allowed when the object is closed.')
        # An error when ASP tries to include something and it fails
        mesg.append('<p>Active Server Pages</font> <font face="Arial" size=2>error \'ASP 0126\'</font>')
        
        # ASPX
        msg = '<b> Description: </b>An unhandled exception occurred during the execution of the'
        msg += ' current web request'
        mesg.append( msg )
        
        # Struts
        mesg.append('] does not contain handler parameter named')
        
        # PHP
        mesg.append('<b>Warning</b>: ')
        mesg.append('No row with the given identifier')
        mesg.append('open_basedir restriction in effect')
        mesg.append("eval()'d code</b> on line <b>")
        mesg.append("Cannot execute a blank command in")
        mesg.append("Fatal error</b>:  preg_replace")
        mesg.append("thrown in <b>")
        mesg.append("#0 {main}")
        mesg.append("Stack trace:")
        mesg.append("</b> on line <b>")
        
        # python
        mesg.append("PythonHandler django.core.handlers.modpython")
        mesg.append("t = loader.get_template(template_name) # You need to create a 404.html template.")
        mesg.append('<h2>Traceback <span>(innermost last)</span></h2>')
        
        # Java
        mesg.append('[java.lang.')
        mesg.append('class java.lang.')
        mesg.append('java.lang.NullPointerException')
        mesg.append('java.rmi.ServerException')
        
        mesg.append('onclick="toggle(\'full exception chain stacktrace\')"')
        mesg.append('at org.apache.catalina')
        mesg.append('at org.apache.coyote.')
        mesg.append('at org.apache.tomcat.')
        mesg.append('at org.apache.jasper.')

        # ruby
        mesg.append('<h1 class="error_title">Ruby on Rails application could not be started</h1>')


        # Coldfusion
        mesg.append('<title>Error Occurred While Processing Request</title></head><body><p></p>')
        mesg.append('<HTML><HEAD><TITLE>Error Occurred While Processing Request</TITLE></HEAD><BODY><HR><H3>')
        mesg.append('<TR><TD><H4>Error Diagnostic Information</H4><P><P>')
        error_msg = '<li>Search the <a href="http://www.macromedia.com/support/coldfusion/" '
        error_msg += 'target="new">Knowledge Base</a> to find a solution to your problem.</li>'
        mesg.append(error_msg)
        
        # http://www.programacion.net/asp/articulo/kbr_execute/
        mesg.append('Server.Execute Error')
        
        # IIS
        mesg.append('<h2 style="font:8pt/11pt verdana; color:000000">HTTP 403.6 - Forbidden: IP address rejected<br>')
        mesg.append('<TITLE>500 Internal Server Error</TITLE>')
       
        return mesg
        
    def grep(self, request, response):
        '''
        Plugin entry point, find the error pages and report them.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if response.is_text_or_html():
            for msg in self._get_error_strings():
                # Remember that httpResponse objects have a faster "__in__" than
                # the one in strings; so string in response.getBody() is slower than
                # string in response
                if msg in response:
                    
                    i = info.info()
                    i.setPluginName(self.getName())
                    
                    # Set a nicer name for the vulnerability
                    name = 'Descriptive error page - "'
                    if len(msg) > 12:
                        name += msg[:12] + '..."'
                    else:
                        name += msg + '"'
                    i.setName( name )
                    
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.setDesc( 'The URL: "' + response.getURL() + '" contains the descriptive error: "' + msg + '"' )
                    i.addToHighlight( msg ) 
                    kb.kb.append( self , 'errorPage' , i )
                    
                    # There is no need to report more than one info for the same result,
                    # the user will read the info object and analyze it even if we report it
                    # only once. If we report it twice, he'll get mad ;)
                    break
                    
            # Now i'll check if I can get a version number from the error page
            # This is common in apache, tomcat, etc...
            if response.getCode() in range(400, 600):
                
                for server, error_regex in self._get_regex_tuples():
                    match = error_regex.search( response.getBody() )
                    if match:
                        match_string = match.groups()[0]
                        if match_string not in self._already_reported_versions:
                            # Save the info obj
                            i = info.info()
                            i.setPluginName(self.getName())
                            i.setName('Error page with information disclosure')
                            i.setURL( response.getURL() )
                            i.setId( response.id )
                            i.setName( 'Error page with information disclosure' )
                            i.setDesc( 'An error page sent this ' + server +' version: "' + match_string + '".'  )
                            i.addToHighlight( server )
                            i.addToHighlight( match_string )
                            kb.kb.append( self , 'server' , i )
                            # Save the string
                            kb.kb.append( self , 'server' , match_string )
                            self._already_reported_versions.append( match_string )

    def _get_regex_tuples( self ):
        '''
        @return: A list of tuples with ( serverName, regexError )
        '''
        if not self._compiled_regex:
            self._compiled_regex.append( ('Apache', re.compile('<address>(.*?)</address>') ) )
            self._compiled_regex.append( ('Apache Tomcat', re.compile('<HR size="1" noshade="noshade"><h3>(.*?)</h3></body>') ) )
            self._compiled_regex.append( ('IIS', re.compile('<a href="http://www.microsoft.com/ContentRedirect.asp\?prd=iis&sbp=&pver=(.*?)&pid=&ID') ) )
            # <b>Version Information:</b>&nbsp;Microsoft .NET Framework Version:1.1.4322.2300; ASP.NET Version:1.1.4322.2300
            self._compiled_regex.append( ('ASP .Net', re.compile('<b>Version Information:</b>&nbsp;(.*?)\n') ) )

        return self._compiled_regex
        
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

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
        This plugin scans every page for error pages, and if possible extracts the web server
        or programming framework information.
        '''
