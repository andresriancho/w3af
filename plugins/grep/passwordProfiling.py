'''
passwordProfiling.py

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
from core.controllers.misc.factory import *
from core.data.getResponseType import *
import urllib
from core.data.parsers.urlParser import *

class passwordProfiling(baseGrepPlugin):
    '''
    Create a list of possible passwords by reading HTTP responses.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        # This is nicer, but htmlParser inherits from SGMLParser that AINT
        # thread safe, So i have to create an instance of htmlParser for every
        # call to testResponse
        #self._htmlParser = htmlParser.htmlParser()
        kb.kb.save( self, 'passwordProfiling', {} )
        
        # names of plugins to run
        ### TODO: develop more plugins, there is a nice ( all python ) metadata reader named hachoir-metadata
        ### it will be usefull for doing A LOT of plugins
        self._pluginsStr = ['html', 'pdf']
        
        # plugin instances, they are created in the first call to self._runPpPlugins
        self._plugins = []
        
        # This are common words I dont want to use as passwords
        self._commonWords = {}
        self._commonWords['en'] = [ 'type', 'that', 'from', 'this', 'been', 'there', 'which', 'line', 'error', 'warning', 'file'\
        'fatal', 'failed', 'open', 'such', 'required', 'directory', 'valid', 'result', 'argument', 'there', 'some']
        
        self._commonWords['es'] = [ 'otro', 'otra', 'para', 'pero', 'hacia', 'algo', 'poder', 'error']
        
        self._commonWords['unknown'] = self._commonWords['en']
        
        
        # Some words that are banned
        self._bannerWords = [ 'Forbidden', 'browsing', 'Index' ]
        
    def _testResponse(self, request, response):
        
        self.is404 = kb.kb.getData( 'error404page', '404' )
        self.lang = kb.kb.getData( 'lang', 'lang' )
        if self.lang == []:
            self.lang = 'unknown'

        if not self.is404( response ) and request.getMethod() in ['POST', 'GET'] and \
        response.getCode() not in [500,401,403]:
            data = self._runPpPlugins( response )
            oldData = kb.kb.getData( 'passwordProfiling', 'passwordProfiling' )
            # "merge" both maps and update the repetitions
            for d in data.keys():
                if d.lower() not in self._commonWords[ self.lang ] \
                and not self._wasSent( request, d ) and len(d) > 3 \
                and d.isalnum() and d not in self._bannerWords:
                    if d in oldData.keys():
                        oldData[ d ] += data[ d ]
                    else:
                        oldData[ d ] = data[ d ]
            
            # save the merged map
            kb.kb.save( self, 'passwordProfiling', oldData )
    
    def _runPpPlugins( self, response ):
        '''
        Runs password profiling plugins to collect data from HTML, TXT, PDF, etc files.
        @parameter response: A httpResponse object
        @return: A map with word:repetitions
        '''
        if len(self._plugins)==0:
            # Create plugins
            for pluginName in self._pluginsStr:
                self._plugins.append( factory( 'plugins.grep.passwordProfilingPlugins.' +  pluginName ) )
        
        res = {}
        for plugin in self._plugins:
            wordMap = plugin.getWords( response )
            if wordMap != None:
                # If a plugin returned something thats not None, then we are done.
                # this plugins only return a something different of None of they found something
                res = wordMap
                break
        return res
        
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
        def sortfunc(x,y):
            return cmp(y[1],x[1])
            
        items = kb.kb.getData( 'passwordProfiling', 'passwordProfiling' ).items()
        if len( items ) != 0:
        
            items.sort(sortfunc)
            om.out.information('Password profiling TOP 100:')
            
            listLen = len(items)
            if listLen > 100:
                xLen = 100
            else:
                xLen = listLen
            
            for i in xrange(xLen):
                om.out.information('- [' + str(i + 1) + '] ' + items[i][0] + ' with ' + str(items[i][1]) + ' repetitions.' )
            

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['grep.lang']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin creates a list of possible passwords by reading responses and counting the most 
        common words.
        '''
