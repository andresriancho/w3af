'''
privateIP.py

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
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
from core.data.bloomfilter.pybloom import ScalableBloomFilter

import core.data.parsers.urlParser as urlParser
import re


class privateIP(baseGrepPlugin):
    '''
    Find private IP addresses on the response body and headers.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # For more info regarding this regular expression, please see:
        # https://sourceforge.net/mailarchive/forum.php?thread_name=1955593874.20090122023644%40
        #mlists.olympos.org&forum_name=w3af-develop
        regex_str = '(?<!\.)(?<!\d)(?:(?:10|127)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|192\.168|169\.'
        regex_str += '254|172\.0?(?:1[6-9]|2[0-9]|3[01]))(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-'
        regex_str += '9]?)){2}(?!\d)(?!\.)'
        self._private_ip_address = re.compile(regex_str)
        self._regex_list = [self._private_ip_address ]

        self._already_inspected = ScalableBloomFilter()
        
    def grep(self, request, response):
        '''
        Plugin entry point. Search for private IPs in the header and the body.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, results are saved to the kb.
        '''
        
        if not ( request.getURL() , request.getData() ) in self._already_inspected:

            #   Only run this once for each combination of URL and data sent to that URL
            self._already_inspected.add( ( request.getURL() , request.getData() ) )

            #
            #   Search for IP addresses in HTTP headers
            #   Get the headers string
            #
            headers_string = response.dumpHeaders()

            #   Match the regular expressions
            for regex in self._regex_list:
                for match in regex.findall(headers_string):

                    # If i'm requesting 192.168.2.111 then I don't want to be alerted about it
                    if match != urlParser.getDomain(response.getURL()):
                        v = vuln.vuln()
                        v.setPluginName(self.getName())
                        v.setURL( response.getURL() )
                        v.setId( response.id )
                        v.setSeverity(severity.LOW)
                        v.setName( 'Private IP disclosure vulnerability' )
                        
                        msg = 'The URL: "' + v.getURL() + '" returned an HTTP header '
                        msg += 'with an IP address: "' +  match + '".'
                        v.setDesc( msg )
                        v['IP'] = match                            
                        v.addToHighlight( match )
                        kb.kb.append( self, 'header', v )       

            #
            #   Search for IP addresses on HTML
            #
            if response.is_text_or_html():
                
                # Performance improvement!
                # Remember that httpResponse objects have a faster "__in__" than
                # the one in strings; so string in response.getBody() is slower than
                # string in response; and regular expression matching is way slower!
                if not (('10.' in response) or ('172.' in response) or \
                    ('192.168.' in response) or ('169.254.' in response)):
                    return
                
                for regex in self._regex_list:
                    for match in regex.findall(response.getBody()):
                        match = match.strip()
                        
                        # Some proxy servers will return errors that include headers in the body
                        # along with the client IP which we want to ignore
                        if re.search("^.*X-Forwarded-For: .*%s" % match, response.getBody(), re.M):
                            continue
                            
                        # If i'm requesting 192.168.2.111 then I don't want to be alerted about it
                        if match != urlParser.getDomain(response.getURL()) and \
                        not request.sent( match ):

                            v = vuln.vuln()
                            v.setPluginName(self.getName())
                            v.setURL( response.getURL() )
                            v.setId( response.id )
                            v.setSeverity(severity.LOW)
                            v.setName( 'Private IP disclosure vulnerability' )
                            
                            msg = 'The URL: "' + v.getURL() + '" returned an HTML document '
                            msg += 'with an IP address: "' +  match + '".'
                            v.setDesc( msg )
                            v['IP'] = match
                            v.addToHighlight( match )
                            kb.kb.append( self, 'html', v )     

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
        self.printUniq( kb.kb.getData( 'privateIP', 'header' ), None )
        self.printUniq( kb.kb.getData( 'privateIP', 'html' ), None )
            
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
        This plugin greps every page body and headers for private IP addresses.
        '''
