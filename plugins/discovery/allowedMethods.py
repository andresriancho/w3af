'''
allowedMethods.py

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

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.w3afException import w3afRunOnce
import core.data.parsers.urlParser as urlParser
from core.data.constants.httpConstants import *
from core.controllers.misc.groupbyMinKey import groupbyMinKey

class allowedMethods(baseDiscoveryPlugin):
    '''
    Enumerate the allowed methods of an URL.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        self._exec = True
        self._alreadyTested = []
        self._badCodes = [ UNAUTHORIZED, NOT_IMPLEMENTED, METHOD_NOT_ALLOWED]
        self._davMethods = [ 'DELETE','PROPFIND','PROPPATCH','COPY','MOVE','LOCK','UNLOCK' ]
        self._commonMethods = [ 'OPTIONS','GET','HEAD','POST', 'TRACE' ]
        
        # User configured variables
        self._execOneTime = False
        self._reportDavOnly = True
        
    def discover(self, fuzzableRequest ):
        '''
        Uses several technics to try to find out what methods are allowed for an URL.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:
            # Run the plugin.
            if self._execOneTime:
                self._exec = False
            
            dp = urlParser.getDomainPath( fuzzableRequest.getURL() )
            if dp not in self._alreadyTested:
                self._alreadyTested.append( dp )
                self._checkMethods( dp )
        return []
    
    def _checkMethods( self, url ):
        allowedMethods = []
        withOptions = False
        
        # First, try to check available methods using OPTIONS, if OPTIONS aint enabled, do it manually
        res = self._urlOpener.OPTIONS( url )
        headers = res.getHeaders()
        if 'allow' in headers:
            allowedMethods = headers['allow'].split(',')
            allowedMethods = [ x.strip() for x in allowedMethods ]
            withOptions = True
        else:
            # 'DELETE' ain't tested ! I don't want to remove anything...
            for method in ['OPTIONS','GET','HEAD','POST','TRACE','PROPFIND','PROPPATCH','COPY','MOVE','LOCK','UNLOCK' ]:
                methodFunctor = getattr( self._urlOpener, method )
                try:
                    response = apply( methodFunctor, (url,) , {} )
                    code = response.getCode()
                except:
                    pass
                else:
                    if code not in self._badCodes:
                        allowedMethods.append( method )
        
        # Added this to make the output a little more readable.
        allowedMethods.sort()
        
        # Check for DAV
        if len( set( allowedMethods ).intersection( self._davMethods ) ) != 0:
            # dav is enabled!
            # Save the results in the KB so that other plugins can use this information
            i = info.info()
            i.setName('Allowed methods for ' + url )
            i.setURL( url )
            i['methods'] = allowedMethods
            i.setDesc( 'The URL "' + url + '" has the following allowed methods, including DAV methods: ' + ', '.join(allowedMethods) )
            kb.kb.append( self , 'dav-methods' , i )
        else:
            # Save the results in the KB so that other plugins can use this information
            i = info.info()
            i.setName('Allowed methods for ' + url )
            i.setURL( url )
            i['methods'] = allowedMethods
            i.setDesc( 'The URL "' + url + '" has the following allowed methods: ' + ', '.join(allowedMethods) )
            kb.kb.append( self , 'methods' , i )
            
        return []
    
    def end( self ):
        '''
        Print the results.
        '''
        # First I get the data from the kb
        all_info_obj = kb.kb.getData( 'allowedMethods', 'methods' )
        dav_info_obj = kb.kb.getData( 'allowedMethods', 'dav-methods' )
        
        # Now I transform it to something I can use with groupbyMinKey
        allMethods = []
        for i in all_info_obj:
            allMethods.append( (i.getURL() , i['methods']) )
        davMethods = []
        for i in dav_info_obj:
            davMethods.append( (i.getURL() , i['methods']) )

        # Now I work the data...
        toShow, type = davMethods, ' DAV'
        if not self._reportDavOnly:
            toShow, type = allMethods, ''
        
        # Make it hashable
        tmp = []
        for url, methodList in toShow:
            tmp.append( (url, ', '.join( methodList ) ) )
        
        resDict, itemIndex = groupbyMinKey( tmp )
            
        for k in resDict:
            if itemIndex == 0:
                # Grouped by URLs
                msg = 'The URL: "%s" has the following' + type + ' methods enabled:'
                om.out.information(msg % k)
            else:
                # Grouped by Methods
                msg = 'The methods: ' + k + ' are enabled on the following URLs:'
                om.out.information(msg)
            
            for i in resDict[k]:
                om.out.information('- ' + i )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Execute plugin only one time'
        h1 = 'Generally the methods allowed for a URL are \
          configured system wide, so executing this plugin only one \
          time is the faster choice. The safest choice is to run it against every URL.'
        o1 = option('execOneTime', self._execOneTime, d1, 'boolean', help=h1)
        
        d2 = 'Only report findings if uncommon methods are found'
        o2 = option('reportDavOnly', self._reportDavOnly, d2, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._execOneTime = optionsMap['execOneTime'].getValue()
        self._reportDavOnly = optionsMap['reportDavOnly'].getValue()

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
        This plugin finds what HTTP methods are enabled for a URI.
        
        Two configurable parameters exist:
            - execOneTime
            - reportDavOnly
        
        If "execOneTime" is set to True, then only the methods in the webroot are enumerated.
        If "reportDavOnly" is set to True, this plugin will only report the enabled method list if DAV methods
        have been found.
        
        The plugin will try to use the OPTIONS method to enumerate all available methods, if that fails, a manual
        enumeration is done, when doing a manual enumeration,  the "DELETE" method ain't tested for safety.
        '''
