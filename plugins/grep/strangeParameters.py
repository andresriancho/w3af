'''
strangeParameters.py

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
import core.data.kb.info as info
import core.data.kb.vuln as vuln

from core.data.bloomfilter.pybloom import ScalableBloomFilter

from core.controllers.w3afException import w3afException
import core.data.parsers.dpCache as dpCache

import re


class strangeParameters(baseGrepPlugin):
    '''
    Grep the HTML response and find URIs that have strange parameters.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # Internal variables
        self._already_reported = ScalableBloomFilter()
        
    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        try:
            dp = dpCache.dpc.getDocumentParserFor( response )
        except w3afException:
            pass
        else:
            # Note:
            # - With parsed_references I'm 100% that it's really something in the HTML
            # that the developer intended to add.
            #
            # - The re_references are the result of regular expressions, which in some cases
            # are just false positives.
            parsed_references, re_references = dp.getReferences()
            
            for ref in parsed_references:
                
                qs = ref.getQueryString()
                
                for param_name in qs:
                    # This for loop is to address the repeated parameter name issue
                    for element_index in xrange(len(qs[param_name])):
                        if self._is_strange( request, param_name, qs[param_name][element_index] )\
                        and ref not in self._already_reported:
                            # Don't repeat findings
                            self._already_reported.add(ref)

                            i = info.info()
                            i.setPluginName(self.getName())
                            i.setName('Strange parameter')
                            i.setURI( ref )
                            i.setId( response.id )
                            msg = 'The URI: "' +  i.getURI() + '" has a parameter named: "' + param_name
                            msg += '" with value: "' + qs[param_name][element_index] + '", which is quite odd.'
                            i.setDesc( msg )
                            i.setVar( param_name )
                            i['parameterValue'] = qs[param_name][element_index]
                            i.addToHighlight(qs[param_name][element_index])

                            kb.kb.append( self , 'strangeParameters' , i )
                            
                        # To find this kind of vulns
                        # http://thedailywtf.com/Articles/Oklahoma-
                        # Leaks-Tens-of-Thousands-of-Social-Security-Numbers,-Other-
                        # Sensitive-Data.aspx
                        if self._is_SQL( request, param_name, qs[param_name][element_index] )\
                        and ref not in self._already_reported:
                            
                            # Don't repeat findings
                            self._already_reported.add(ref)
                            
                            v = vuln.vuln()
                            v.setPluginName(self.getName())
                            v.setName('Parameter has SQL sentence')
                            v.setURI( ref )
                            v.setId( response.id )
                            msg = 'The URI: "' +  v.getURI() + '" has a parameter named: "' + param_name
                            msg +='" with value: "' + qs[param_name][element_index] + '", which is a SQL sentence.'
                            v.setDesc( msg )
                            v.setVar( param_name )
                            v['parameterValue'] = qs[param_name][element_index]
                            v.addToHighlight(qs[param_name][element_index])
                            kb.kb.append( self , 'strangeParameters' , v )
    
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
        self.printUniq( kb.kb.getData( 'strangeParameters', 'strangeParameters' ), 'VAR' )

    def _is_SQL(self, request, parameter, value):
        '''
        @return: True if the parameter value contains SQL sentences
        '''
        regex = '(SELECT .*? FROM|INSERT INTO .*? VALUES|UPDATE .*? SET .*? WHERE)'
        for match in re.findall( regex, value, re.IGNORECASE):
            if not request.sent( match ):
                return True
        
        return False

    def _is_strange(self, request, parameter, value):
        '''
        @return: True if the parameter value is strange
        '''
        _strange_parameter_re = []

        # Seems to be a function
        _strange_parameter_re.append('\w+\(.*?\)')
        # Add more here...
        #_strange_parameter_re.append('....')

        for regex in _strange_parameter_re:
            for match in re.findall( regex, value ):
                if not request.sent( match ):
                    return True
        
        splitted_value = [ x for x in re.split( r'([a-zA-Z0-9. ]+)', value ) if x != '' ]
        if len( splitted_value ) > 4:
            if not request.sent( value ):
                return True
        
        return False
    
        
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
        This plugin greps all responses and tries to identify URIs with strange parameters, some examples of strange
        parameters are:
            - http://a/?b=method(a,c)
            - http://a/?c=x|y|z|d
        '''
