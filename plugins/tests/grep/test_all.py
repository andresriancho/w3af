'''
test_all.py

Copyright 2011 Andres Riancho

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

import unittest
import os
import cProfile

import core.controllers.w3afCore
from core.controllers.coreHelpers.fingerprint_404 import is_404

from core.data.url.httpResponse import httpResponse
from core.data.request.fuzzableRequest import fuzzableRequest
from core.data.parsers.urlParser import url_object


class test_all(unittest.TestCase):
    
    def setUp(self):
        #
        #   Init
        #
        self.url_str = 'http://localhost:631/'
        self.url_inst = url_object( self.url_str )
        spam = httpResponse(200, '', {}, self.url_inst, self.url_inst)

        try:
            spam = httpResponse(200, '', {}, self.url_inst, self.url_inst)
            is_404(spam)
        except:
            pass

        self._w3af = core.controllers.w3afCore.w3afCore()
        self._plugins = []
        for pname in self._w3af.plugins.getPluginList('grep'):
            self._plugins.append( self._w3af.plugins.getPluginInstance(pname, 'grep') )

    def test_options_for_grep_plugins(self):
        '''
        We're not going to assert anything here. What just want to see if
        the plugins implement the following methods:
            - getOptions()
            - setOptions()
            - getPluginDeps()
            - getLongDesc()
            
        And don't crash in any way when we call them.
        '''
        for plugin in self._plugins:
            o = plugin.getOptions()
            plugin.setOptions( o )
            
            plugin.getPluginDeps()
            plugin.getLongDesc()
            
            plugin.end()
                
    def test_all_grep_plugins(self):
        '''
        Run a set of 5 html files through all grep plugins. As with the previous
        test, the only thing we want to see is if the grep plugin crashes or not.
        
        We're not asserting any results. 
        '''
        def profile_me():
            '''
            To be profiled
            '''
            for _ in xrange(1):
                for counter in xrange(1,5):
                    
                    file_name = 'test-' + str(counter) + '.html'
                    file_path = os.path.join('plugins','tests','grep',file_name)
                    
                    body = file( file_path ).read()
                    response = httpResponse(200, body, {'Content-Type': 'text/html'},
                                            url_object( self.url_str + str(counter) ),
                                            url_object( self.url_str + str(counter) ) )

                    request = fuzzableRequest(self.url_inst)
                    for pinst in self._plugins:
                        pinst.grep( request, response )

        #
        #   The only test here is that we don't get any traceback
        #
        profile_me()

        #
        #   For profiling
        #
        #cProfile.run('profile_me()', 'output.stats')


