'''
export_requests.py

Copyright 2012 Andres Riancho

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

import core.data.kb.knowledgeBase as kb


from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
from core.controllers.w3afException import w3afException

# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.request.wsPostDataRequest import wsPostDataRequest


class export_requests(baseOutputPlugin):
    '''
    Export the fuzzable requests found during discovery to a file.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseOutputPlugin.__init__(self)
        self.output_file = 'output-requests.csv'

    def do_nothing(self, *args, **kwds): pass

    debug = logHttp = vulnerability = do_nothing
    information = error = console = debug = logEnabledPlugins = do_nothing
    
    def end(self):
        '''
        Exports a list of fuzzable requests to the user configured file.
        '''
        fuzzable_request_list = kb.kb.getData('urls', 'fuzzable_requests')
        
        filename = self.output_file
        try:
            file = open(filename, 'w')
            file.write('HTTP-METHOD,URI,POSTDATA\n')
        
            for fr in fuzzable_request_list:
                # TODO: How shall we export wsPostDataRequests?
                if not isinstance(fr, wsPostDataRequest):
                    file.write(fr.export() + '\n')
            
            file.close()
        except Exception, e:
            msg = 'An exception was raised while trying to export fuzzable requests to the'
            msg += ' output file.' + str(e)
            raise w3afException( msg )        

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exports all discovered HTTP requests (URL, Method, Params)
        to the given file (CSV) which can then be imported in another scan by
        using the discovery.importResults.
        
        One configurable parameter exists:
            - output_file
        '''

    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        output_file = OptionList['output_file'].getValue()
        if not output_file:
            raise w3afException('You need to configure an output file.')
        else:
            self.output_file = output_file

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'The name of the output file where the HTTP requests will be saved'
        o1 = option('output_file', self.output_file, d1, 'string')
        
        ol = optionList()
        ol.add(o1)
        return ol
