'''
GrepPlugin.py

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
import core.data.kb.config as cf

from core.controllers.plugins.plugin import Plugin


class GrepPlugin(Plugin):
    '''
    This is the base class for grep plugins, all grep plugins should
    inherit from it and implement the following method:
        1. grep(request, response)

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        Plugin.__init__(self)

    def grep_wrapper(self, fuzzable_request, response):
        '''
        This method tries to find patterns on responses.
        
        This method CAN be implemented on a plugin, but its better to
        do your searches in _testResponse().
        
        @param response: This is the httpResponse object to test.
        @param fuzzable_request: This is the fuzzable request object that
            generated the current response being analyzed.
        @return: If something is found it must be reported to the Output
            Manager and the KB.
        '''
        if response.getFromCache():
            return
        
        if response.getURL().getDomain() in cf.cf.getData('targetDomains'):
            self.grep(fuzzable_request, response)
    
    def grep(self, fuzzable_request, response):
        '''
        Analyze the response.
        
        @param fuzzable_request: The request that was sent
        @param response: The HTTP response obj
        '''
        raise NotImplementedError('Plugin "%s" must not implement required '
                                  'method grep' % self.__class__.__name__)
                    
    def set_url_opener(self, foo):
        pass
        
    def getType(self):
        return 'grep'
