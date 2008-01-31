'''
fastScan.py

Copyright 2007 Andres Riancho

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

from profiles.profile import profile as profile

class fastScan( profile ):
    '''
    This is a fast scan profile.
    '''
    def __init__( self ):
        profile.__init__( self )
        
    def getName( self ):
        return 'fastScan'
        
    def getDesc( self ):
        '''
        @return: A ONE LINE description of the scan profile
        '''
        return 'Perform a fast scan of the target site, using only a few discovery plugins and the fastest audit plugins.'
        
    def getLongDesc( self ):
        '''
        @return: A LONG description of the scan profile
        '''
        res = '''
        Perform a fast scan of the target using the following discovery plugins:
        '''
        for i in self._getDiscoveryPlugins():
            res += '\t\t\t- ' + i + '\n'
        res += 'And these audit plugins:'
        for i in self._getAuditPlugins():
            res += '\t\t\t- ' + i + '\n'
    
    def getEnabledPlugins( self , type ):
        '''
        @return: A list of activated $type plugins.
        '''
        if type == 'discovery':
            return ['yahooSiteExplorer']
        elif type == 'audit':
            return ['sqli', 'xss']
        # don't forget this !!
        elif type == 'output':
            return ['console']
        else:
            return []
            
    def getPluginOptions( self, pluginName, type ):
        self._setDefaultPluginOptions()
        return self._defaultPluginOptions[type][pluginName]
