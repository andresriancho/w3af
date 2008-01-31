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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.parsers.urlParser as uparser
from core.data.getResponseType import *
import re

class newline(baseGrepPlugin):
    '''
    Identify the type of newline used in every page.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._unix = re.compile( '[^\r]\n' )
        self._windows = re.compile( '\r\n' )
        self._mac = re.compile( '\r[^\n]' )
        
    def _testResponse(self, request, response):
        self.is404 = kb.kb.getData( 'error404page', '404' )
        if isTextOrHtml(response.getHeaders()) and request.getMethod() in ['GET','POST']\
        and not self.is404( response ):
            unix = self._unix.findall( response.getBody() )
            windows = self._windows.findall( response.getBody() )
            mac = self._mac.findall( response.getBody() )
            
            i = info.info()
            i.setURL( response.getURL() )
            i.setId( response.id )
            
            msg = ''
            if len( unix ) > 0:
                if len( windows ) == 0 and len( mac ) == 0:
                    msg = 'The body of the URL: '  + response.getURL() + ' was created using a unix editor.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'unix', i )
                if len( windows ) != 0 and len( unix ) > len( windows ):
                    msg = 'The body of the URL: '  + response.getURL() + ' was mainly created using a unix editor but newlines with windows style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'unix_windows', i )
                if len( mac ) != 0 and len( unix ) > len( mac ):
                    msg = 'The body of the URL: '  + response.getURL() + ' was mainly created using a unix editor but newlines with mac style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'unix_mac', i )
            
            # Maybe I should think about doing this in a for loop or something...
            
            if len( windows ) > 0:
                if len( unix ) == 0 and len( mac ) == 0:
                    msg = 'The body of the URL: '  + response.getURL() + ' was created using a windows editor.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'windows', i )
                if len( unix ) != 0 and len( windows ) > len( unix ):
                    msg = 'The body of the URL: '  + response.getURL() + ' was mainly created using a windows editor but newlines with unix style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'windows_unix', i )
                elif len( mac ) != 0 and len( windows ) > len( mac ):
                    msg = 'The body of the URL: '  + response.getURL() + ' was mainly created using a windows editor but newlines with mac style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'windows_mac', i )
            
            if len( mac ) > 0:
                if len( windows ) == 0 and len( unix ) == 0:
                    msg = 'The body of the URL: '  + response.getURL() + ' was created using a mac editor.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'mac', i )
                if len( windows ) != 0 and len( mac ) > len( windows ):
                    msg = 'The body of the URL: '  + response.getURL() + ' was mainly created using a mac editor but newlines with windows style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'mac_windows', i )
                elif len( unix ) != 0 and len( mac ) > len( unix ):
                    msg = 'The body of the URL: '  + response.getURL() + ' was mainly created using a mac editor but newlines with unix style also were found.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'mac_unix', i )
            
            if len( mac ) > 0 and len( windows ) > 0 and len( unix ) > 0:
                # This is a mess!
                msg = 'The body of the URL: '  + response.getURL() + ' has the three types of newline style, unix, mac and windows.'
                i.setDesc( msg )
                kb.kb.append( self, 'all', i )
            
            if len( mac ) == 0 and len( windows ) == 0 and len( unix ) == 0:
                msg = 'The body of the URL: '  + response.getURL() + ' has no newlines.'
                i.setDesc( msg )
                kb.kb.append( self, 'none', i )
                
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
        # Print the results to the user
        prettyMsg = {}
        prettyMsg['unix'] = 'The body of the following URLs was created using a unix editor:'
        prettyMsg['unix_mac'] = 'The body of the following URLs was mainly created using a unix editor but newlines with mac style also were found:'
        prettyMsg['unix_windows']= 'The body of the following URLs was mainly created using a unix editor but newlines with windows style also were found:'
        prettyMsg['windows'] = 'The body of the following URLs was created using a windows editor:'
        prettyMsg['windows_unix'] = 'The body of the following URLs was mainly created using a windows editor but newlines with unix style also were found:'
        prettyMsg['windows_mac'] = 'The body of the following URLs was mainly created using a windows editor but newlines with mac style also were found:'
        prettyMsg['mac'] = 'The body of the following URLs was created using a mac editor:'
        prettyMsg['mac_windows'] = 'The body of the following URLs was mainly created using a mac editor but newlines with windows style also were found:'
        prettyMsg['mac_unix'] = 'The body of the following URLs was mainly created using a mac editor but newlines with unix style also were found:'
        prettyMsg['all'] = 'The body of the following URLs has the three types of newline style, unix, mac and windows:'
        prettyMsg['none'] = 'The body of the following URLs has no newlines:'
    
        for type in ['unix', 'unix_mac', 'unix_windows', 'windows', 'windows_unix', 'windows_mac',\
        'mac', 'mac_windows', 'mac_unix', 'all', 'none']:
            inform = []
            for v in kb.kb.getData( 'newline', type ):
                inform.append( v.getURL() )
            
            inform = list( set( inform ) )
            
            if len( inform ):
                om.out.information( prettyMsg[ type ] )
                inform.sort()
                for i in inform:
                    om.out.information( '- ' + i )
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.error404page']
    
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
