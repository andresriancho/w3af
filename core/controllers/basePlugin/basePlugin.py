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

import sys
import threading

import core.controllers.outputManager as om
import core.data.kb.vuln as vuln

from core.data.options.optionList import optionList
from core.controllers.configurable import configurable
from core.controllers.threads.threadManager import thread_manager
from core.controllers.w3afException import w3afException, w3afMustStopOnUrlError


class basePlugin(configurable):
    '''
    This is the base class for ALL plugins, all plugins should inherit from it 
    and implement the following method :
        1. getPluginDeps()
        
    Please note that this class is a configurable object, so it must implement:
        1. setOptions( OptionList )
        2. getOptions()
        
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        '''
        Create some generic attributes that are going to be used by most plugins.
        '''
        self._uri_opener = None
        self._tm = thread_manager
        self._plugin_lock = threading.RLock()

    def setUrlOpener( self, urlOpener):
        '''
        This method should not be overwritten by any plugin (but you are free
        to do it, for example a good idea is to rewrite this method to change
        the UrlOpener to do some IDS evasion technic).
        
        This method takes a CustomUrllib object as parameter and assigns it 
        to itself. Then, on the testUrl method you use 
        self.CustomUrlOpener._custom_urlopen(...) 
        to open a Url and you are sure that the plugin is using the user 
        supplied settings (proxy, user agent, etc).
        
        @return: No value is returned.
        '''
        self._uri_opener = UrlOpenerProxy(urlOpener, self)

    def setOptions( self, optionsList ):
        '''
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the options that were retrieved from the plugin using getOptions()
        
        This method must be implemented in every plugin that wishes to have user
        configurable options. 
        
        @return: No value is returned.
        '''
        pass
        
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        return ol

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be 
                 run before the current one. Only plugins with dependencies
                 should override this method.
        '''
        return []

    def getDesc( self ):
        '''
        @return: A description of the plugin.
        
        >>> b = basePlugin()
        >>> b.__doc__ = 'abc'
        >>> b.getDesc()
        'abc'
        >>> b = basePlugin()
        >>> b.__doc__ = '    abc\t'
        >>> b.getDesc()
        'abc'
        '''
        if self.__doc__ is not None:
            res2 = self.__doc__.replace( '\t' , '' )
            res2 = self.__doc__.replace( '    ' , '' )
            res = ''.join ( [ i for i in res2.split('\n') if i != '' and
                             '@author' not in i ] )
        else:
            res = ''
        return res
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        raise w3afException('Plugin is not implementing required method getLongDesc' )
    
    def print_uniq( self, infoObjList, unique ):
        '''
        Print the items of infoObjList to the user interface
        
        @parameter infoObjList: A list of info objects
        @parameter unique: Defines whats unique:
            - 'URL': The URL must be unique
            - 'VAR': The url/variable combination must be unique
            - None: Print all vulns, nothing should be unique
            
        >>> b = basePlugin()
        >>> v1 = vuln.vuln()
        >>> v1.setDesc('hello')
        >>> v2 = vuln.vuln()
        >>> v2.setDesc('world')
        >>> info_obj = [ v1, v2 ]
        >>> b.print_uniq(info_obj, None) is None
        True
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
        
        elif unique is None:
            inform = infoObjList
            
        else:
            om.out.error('basePlugin.print_uniq(): Unknown unique parameter value.')

        # Print the list            
        for i in inform:
            if isinstance(i, vuln.vuln):
                om.out.vulnerability( i.getDesc(), severity=i.getSeverity() )
            else:
                om.out.information( i.getDesc() )
            
    def __eq__( self, other ):
        '''
        This function is called when extending a list of plugin instances.
        '''
        return self.__class__.__name__ == other.__class__.__name__
    
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

    def handleUrlError(self, url_error):
        '''
        Handle UrlError exceptions raised when requests are made.
        Subclasses should redefine this method for a more refined
        behavior and must respect the return value format.
        
        @param url_error: w3afMustStopOnUrlError exception instance
        @return: (stopbubbling, result). The 1st is a boolean value
            that indicates the caller if the original error should
            stop bubbling or not. The 2nd is the result to be
            returned by the caller. Note that only makes sense
            when `stopbubbling` is True.
        '''
        om.out.error('There was an error while requesting "%s". Reason: %s' % 
                     (url_error.req.get_full_url(), url_error.msg))
        return (False, None)

    def _send_mutants_async(self, func, iterable, callback):
        func = return_args(func)
        for (mutant,), http_response in self._tm.threadpool.imap_unordered(func, iterable):
            callback(mutant, http_response)
    

class UrlOpenerProxy(object):
    '''
    Proxy class for urlopener objects such as xUrllib instances.
    '''
    
    def __init__(self, url_opener, plugin_inst):
        self._url_opener = url_opener
        self._plugin_inst = plugin_inst
    
    def __getattr__(self, name):
        def meth(*args, **kwargs):
            try:
                return attr(*args, **kwargs)
            except w3afMustStopOnUrlError, w3aferr:
                stopbubbling, result = \
                        self._plugin_inst.handleUrlError(w3aferr)
                if not stopbubbling:
                    try:
                        exc_info = sys.exc_info()
                        raise exc_info[0], exc_info[1], exc_info[2]
                    finally:
                        del exc_info
                return result
        attr = getattr(self._url_opener, name)
        return meth if callable(attr) else attr

class return_args(object):
    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args):
        return args, self.func(*args)
