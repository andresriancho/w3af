'''
newline.py

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

from core.controllers.coreHelpers.fingerprint_404 import is_404
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

import re


class newline(baseGrepPlugin):
    '''
    Identify the type of newline used in every page.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)

        # User configured parameters
        self._mixed_only = True

        # New line style
        self._unix = re.compile( '[^\r]\n' )
        self._windows = re.compile( '\r\n' )
        self._mac = re.compile( '\r[^\n]' )
        
    def grep(self, request, response):
        '''
        Plugin entry point. Analyze the new line convention of the site.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if response.is_text_or_html() and request.getMethod() in ['GET', 'POST']\
        and not is_404( response ):
            unix = self._unix.findall( response.getBody() )
            windows = self._windows.findall( response.getBody() )
            mac = self._mac.findall( response.getBody() )
            
            i = info.info()
            i.setName('Newline information')
            i.setURL( response.getURL() )
            i.setId( response.id )
            
            msg = ''
            if len( unix ) > 0 and len(unix) >= len(windows) and len(unix) >= len(mac):
                if len( windows ) == 0 and len( mac ) == 0 and not self._mixed_only:
                    msg = 'The body of the URL: "'  + response.getURL() + '"'
                    msg += ' was created using a unix editor.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'unix', i )
                if len( windows ) != 0 and len( unix ) > len( windows ):
                    msg = 'The body of the URL: "'  + response.getURL() + '" was mainly created'
                    msg += ' using a unix editor but newlines with windows style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'unix_windows', i )
                if len( mac ) != 0 and len( unix ) > len( mac ):
                    msg = 'The body of the URL: "'  + response.getURL() + '" was mainly created'
                    msg += ' using a unix editor but newlines with mac style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'unix_mac', i )
            
            # Maybe I should think about doing this in a for loop or something...
            
            elif len( windows ) > 0 and len(windows) >= len(unix) and len(windows) >= len(mac):
                if len( unix ) == 0 and len( mac ) == 0  and not self._mixed_only:
                    msg = 'The body of the URL: "'  + response.getURL() + '" was created '
                    msg += 'using a windows editor.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'windows', i )
                if len( unix ) != 0 and len( windows ) > len( unix ):
                    msg = 'The body of the URL: "'  + response.getURL() + '" was mainly created'
                    msg += ' using a windows editor but newlines with unix style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'windows_unix', i )
                elif len( mac ) != 0 and len( windows ) > len( mac ):
                    msg = 'The body of the URL: "'  + response.getURL() + '" was mainly created'
                    msg += ' using a windows editor but newlines with mac style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'windows_mac', i )
            
            elif len( mac ) > 0 and len(mac) >= len(unix) and len(mac) >= len(windows):
                if len( windows ) == 0 and len( unix ) == 0  and not self._mixed_only:
                    msg = 'The body of the URL: "'  + response.getURL() + '" was created using '
                    msg += 'a mac editor.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'mac', i )
                if len( windows ) != 0 and len( mac ) > len( windows ):
                    msg = 'The body of the URL: "'  + response.getURL() + '" was mainly created '
                    msg += 'using a mac editor but newlines with windows style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'mac_windows', i )
                elif len( unix ) != 0 and len( mac ) > len( unix ):
                    msg = 'The body of the URL: "'  + response.getURL() + '" was mainly created '
                    msg += 'using a mac editor but newlines with unix style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'mac_unix', i )

            # This is a mess!            
            if len( mac ) > 0 and len( windows ) > 0 and len( unix ) > 0:
                msg = 'The body of the URL: "'  + response.getURL() + '" has the '
                msg += 'three types of newline style, unix, mac and windows.'
                i.setDesc( msg )
                kb.kb.append( self, 'all', i )

                
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        d1 = 'Only report mixed newlines.'
        h1 = 'If "mixedOnly" is enabled this plugin will only create objects in the knowledge base'
        h1 += ' when the page under analysis has mixed new lines (i.e windows/unix).'
        o1 = option('mixedOnly', self._mixed_only , d1, 'boolean', help=h1)
        
        ol = optionList()
        ol.add(o1)
        
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Print the results to the user
        pretty_msg = {}
        pretty_msg['unix'] = 'The body of the following URLs was created using a unix editor:'
        pretty_msg['unix_mac'] = 'The body of the following URLs was mainly created using a '
        pretty_msg['unix_mac'] += 'unix editor but newlines with mac style also were found:'

        pretty_msg['unix_windows'] = 'The body of the following URLs was mainly created using a '
        pretty_msg['unix_windows'] += 'unix editor but newlines with windows style also were found:'

        pretty_msg['windows'] = 'The body of the following URLs was created using a windows editor:'

        pretty_msg['windows_unix'] = 'The body of the following URLs was mainly created using a '
        pretty_msg['windows_unix'] += 'windows editor but newlines with unix style also were found:'

        pretty_msg['windows_mac'] = 'The body of the following URLs was mainly created using a '
        pretty_msg['windows_mac'] += 'windows editor but newlines with mac style also were found:'

        pretty_msg['mac'] = 'The body of the following URLs was created using a mac editor:'
        pretty_msg['mac_windows'] = 'The body of the following URLs was mainly created using a '
        pretty_msg['mac_windows'] += 'mac editor but newlines with windows style also were found:'

        pretty_msg['mac_unix'] = 'The body of the following URLs was mainly created using a '
        pretty_msg['mac_unix'] += 'mac editor but newlines with unix style also were found:'

        pretty_msg['all'] = 'The body of the following URLs has the three types of newline '
        pretty_msg['all'] += 'style, unix, mac and windows:'
    
        for new_line_type in pretty_msg.keys():
            inform = []
            for v in kb.kb.getData( 'newline', new_line_type ):
                inform.append( v.getURL() )
            
            inform = list( set( inform ) )
            
            if len( inform ):
                om.out.information( pretty_msg[ new_line_type ] )
                inform.sort()
                for i in inform:
                    om.out.information( '- ' + i )
        
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
        This plugin identifies the type of newline used in every page. At the end, it will report if a page was
        generated using a Windows, Linux or Mac editor; or maybe a combination of two.
        
        Note: I dont know if this plugin has any real use... but it was one of a group of many ideas... 
        maybe sometime this rather useless plugin will raise from the dead and tell us what it's purpose is.
        '''
