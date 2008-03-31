'''
basePlugin.py

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

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.controllers.threads.threadManager import threadManagerObj as tm
from core.controllers.configurable import configurable
import core.data.kb.vuln as vuln

class basePlugin(configurable):
    '''
    This is the base class for ALL plugins, all plugins should inherit from it 
    and implement the following method :
        1. getPluginDeps()
        
    Please note that this class is a configurable object, so it must implement:
        1. setOptions( OptionList )
        2. getOptionsXML()
        
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        self._urlOpener = None
        self._tm = tm

    def setUrlOpener( self, urlOpener):
        '''
        This method should not be overwritten by any plugin (but you are free to do it, for example
        a good idea is to rewrite this method to change the UrlOpener to do some IDS evasion technic).
        
        This method takes a CustomUrllib object as parameter and assigns it to itself. 
        Then, on the testUrl method you use self.CustomUrlOpener._custom_urlopen(...) 
        to open a Url and you are sure that the plugin is using the user supplied
        settings (proxy, user agent, etc).
        
        @return: No value is returned.
        '''
        self._urlOpener = urlOpener
        

    def setOptions( self, OptionsMap ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptionsXML()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method setOptions' )
        
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        This method is just here for back compatibility; please use getOptions.
        
        @return: XML with the plugin options.
        ''' 
        return  str(self.getOptions())

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        raise w3afException('Plugin is not implementing required method getOptions' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be 
        runned before the current one.
        '''
        raise w3afException('Plugin is not implementing required method getPluginDeps' )

    def getDesc( self ):
        '''
        @return: A description of the plugin.
        '''
        if self.__doc__ != None:
            res2 = self.__doc__.replace( '\t' , '' )
            res2 = self.__doc__.replace( '    ' , '' )
            res = ''.join ( [ i for i in res2.split('\n') if i != '' and '@author' not in i ] )
        else:
            res = ''
        return res
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        raise w3afException('Plugin is not implementing required method getLongDesc' )
    
    def printUniq( self, infoObjList, unique ):
        '''
        Print the items of infoObjList to the user interface
        
        @parameter infoObjList: A list of info objects
        @parameter unique: Defines whats unique:
            - 'URL': The URL must be unique
            - 'VAR': The url/variable combination must be unique
            - None: Print all vulns, nothing should be unique
        '''

        # Create the list of things to inform
        inform = []
        if unique == 'URL':
            reportedURLs = []
            for i in infoObjList:
                if i.getURL() not in reportedURLs:
                    reportedURLs.append( i.getURL() )
                    inform.append( i )
        
        elif unique == 'VAR':
            reportedVARs = []
            for i in infoObjList:
                if (i.getURL(), i.getVar()) not in reportedVARs:
                    reportedVARs.append( (i.getURL(), i.getVar()) )
                    inform.append( i )
        
        elif unique == None:
            inform = infoObjList
            
        else:
            om.out.error('basePlugin.printUniq(): Unknown unique parameter value.')

        # Print the list            
        for i in inform:
            if isinstance(i, vuln.vuln):
                om.out.vulnerability( i.getDesc() )
            else:
                om.out.information( i.getDesc() )
            
    def _sendMutant( self, mutant, analyze=True, grepResult=True ):
        '''
        Sends a mutant to the remote web server.
        '''
        url = mutant.getURI()
        data = mutant.getData()
        headers = mutant.getHeaders()
        # Also add the cookie header.
        cookie = mutant.getCookie()
        if cookie:
            headers['Cookie'] = str(cookie)

        args = ( url, )
        method = mutant.getMethod()
        
        functor = getattr( self._urlOpener , method )
        # run functor , run !   ( forest gump flash )
        res = apply( functor, args, {'data': data, 'headers': headers, 'grepResult': grepResult } )
        
        if analyze:
            self._analyzeResult( mutant, res )
        return res
    
    def __eq__( self, other ):
        '''
        This function is called when extending a list of plugin instances.
        '''
        if self.__class__.__name__ == other.__class__.__name__:
            return True
        else:
            return False
    
    def end( self ):
        '''
        This method is called by w3afCore to let the plugin know that it wont be used
        anymore. This is helpfull to do some final tests, free some structures, etc.
        '''
        pass
        
    def getType( self ):
        return 'plugin'

    def getName( self ):
        return self.__class__.__name__
