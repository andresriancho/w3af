'''
password_profiling.py

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
from __future__ import with_statement

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.misc.factory import factory


class password_profiling(GrepPlugin):
    '''
    Create a list of possible passwords by reading HTTP response bodies.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    COMMON_WORDS = {'en': set([ 'type', 'that', 'from', 'this', 'been', 'there',
                                'which', 'line', 'error', 'warning', 'file',
                                'fatal', 'failed', 'open', 'such', 'required', 
                                'directory', 'valid', 'result', 'argument',
                                'there', 'some']),
                    
                    'es': set([ 'otro', 'otra', 'para', 'pero', 'hacia', 'algo',
                                'poder','error']),
                    
                    }
    COMMON_WORDS['unknown'] = COMMON_WORDS['en']
    
    BANNED_WORDS = set(['forbidden', 'browsing', 'index'])
    
    
    def __init__(self):
        GrepPlugin.__init__(self)
        kb.kb.save( self, 'password_profiling', {} )
        
        #TODO: develop more plugins, there is a, pure-python metadata reader named
        #      hachoir-metadata it will be useful for writing A LOT of plugins
        
        # Plugins to run
        self._plugins_names_dict = ['html', 'pdf']
        self._plugins = []
        
        
    def grep(self, request, response):
        '''
        Plugin entry point. Get responses, analyze words, create dictionary.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None.
        '''
        # Initial setup
        lang = kb.kb.getData( 'lang', 'lang' ) or 'unknown'

        # I added the 404 code here to avoid doing some is_404 lookups
        if response.getCode() not in [500, 401, 403, 404] \
        and not is_404(response) \
        and request.get_method() in ['POST', 'GET']:
            
            # Run the plugins
            data = self._run_plugins(response)
            
            with self._plugin_lock:
                old_data = kb.kb.getData( 'password_profiling', 'password_profiling' )
                
                # "merge" both maps and update the repetitions
                for d in data:
                    
                    if len(d) >= 4 and d.isalnum() and \
                        not d.isdigit() and \
                        d.lower() not in self.BANNED_WORDS and \
                        d.lower() not in self.COMMON_WORDS[lang] and \
                        not request.sent( d ):
                        
                        if d in old_data:
                            old_data[ d ] += data[ d ]
                        else:
                            old_data[ d ] = data[ d ]
                
                #   If the dict grows a lot, I want to trim it. Basically, if 
                #   it grows to a length of more than 2000 keys, I'll trim it
                #   to 1000 keys.
                if len( old_data ) > 2000:
                    def sortfunc(x_obj, y_obj):
                        return cmp(y_obj[1], x_obj[1])
                
                    items = old_data.items()
                    items.sort(sortfunc)
                    
                    items = items[:1000]
                    
                    new_data = {}
                    for key, value in items:
                        new_data[key] = value
                        
                else:
                    new_data = old_data
                
                # save the updated map
                kb.kb.save(self, 'password_profiling', new_data)

    
    def _run_plugins( self, response ):
        '''
        Runs password profiling plugins to collect data from HTML, TXT, PDF, etc files.
        @parameter response: A httpResponse object
        @return: A map with word:repetitions
        '''
        # Create plugin instances only once
        if not self._plugins:
            for plugin_name in self._plugins_names_dict:
                plugin_klass = 'plugins.grep.password_profiling_plugins.%s'
                plugin_instance = factory( plugin_klass % plugin_name )
                self._plugins.append( plugin_instance )
        
        res = {}
        for plugin in self._plugins:
            wordMap = plugin.getWords( response )
            if wordMap is not None:
                # If a plugin returned something thats not None, then we are done.
                # this plugins only return a something different of None of they 
                # found something
                res = wordMap
                break
        
        return res
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        def sortfunc(x_obj, y_obj):
            return cmp(y_obj[1], x_obj[1])
        
        profiling_data = kb.kb.getData( 'password_profiling', 'password_profiling' )
        
        # This fixes a very strange bug where for some reason the kb doesn't 
        # have a dict anymore (threading issue most likely) Seen here:
        # https://sourceforge.net/apps/trac/w3af/ticket/171745
        if isinstance(profiling_data, dict):

            items = profiling_data.items()
            if len( items ) != 0:
            
                items.sort(sortfunc)
                om.out.information('Password profiling TOP 100:')
                
                list_length = len(items)
                if list_length > 100:
                    xLen = 100
                else:
                    xLen = list_length
                
                for i in xrange(xLen):
                    msg = '- [' + str(i + 1) + '] ' + items[i][0] + ' with ' + str(items[i][1]) 
                    msg += ' repetitions.'
                    om.out.information( msg )
            

    def get_plugin_deps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['grep.lang']
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin creates a list of possible passwords by reading responses
        and counting the most common words.
        '''
