'''
strange_parameters.py

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
import re

import core.data.parsers.dpCache as dpCache
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.controllers.exceptions import w3afException


class strange_parameters(GrepPlugin):
    '''
    Grep the HTML response and find URIs that have strange parameters.
      
    @author: Andres Riancho ((andres.riancho@gmail.com))
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        
        # Internal variables
        self._already_reported = ScalableBloomFilter()
        
    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        try:
            dp = dpCache.dpc.get_document_parser_for( response )
        except w3afException:
            pass
        else:
            # Note:
            # - With parsed_references I'm 100% that it's really something in the HTML
            # that the developer intended to add.
            #
            # - The re_references are the result of regular expressions, which in some cases
            # are just false positives.
            parsed_references, _ = dp.get_references()
            
            for ref in parsed_references:
                
                qs = ref.querystring
                
                for param_name in qs:
                    # This for loop is to address the repeated parameter name issue
                    for element_index in xrange(len(qs[param_name])):
                        if self._is_strange( request, param_name, qs[param_name][element_index] )\
                        and (ref.uri2url(), param_name) not in self._already_reported:
                            # Don't repeat findings
                            self._already_reported.add( (ref.uri2url(), param_name) )

                            i = info.info()
                            i.setPluginName(self.get_name())
                            i.set_name('Strange parameter')
                            i.setURI( ref )
                            i.set_id( response.id )
                            msg = 'The URI: "' +  i.getURI() + '" has a parameter named: "' + param_name
                            msg += '" with value: "' + qs[param_name][element_index] + '", which is quite odd.'
                            i.set_desc( msg )
                            i.set_var( param_name )
                            i['parameterValue'] = qs[param_name][element_index]
                            i.addToHighlight(qs[param_name][element_index])

                            kb.kb.append( self , 'strange_parameters' , i )
                            
                        # To find this kind of vulns
                        # http://thedailywtf.com/Articles/Oklahoma-
                        # Leaks-Tens-of-Thousands-of-Social-Security-Numbers,-Other-
                        # Sensitive-Data.aspx
                        if self._is_SQL( request, param_name, qs[param_name][element_index] )\
                        and ref not in self._already_reported:
                            
                            # Don't repeat findings
                            self._already_reported.add(ref)
                            
                            v = vuln.vuln()
                            v.setPluginName(self.get_name())
                            v.set_name('Parameter has SQL sentence')
                            v.setURI( ref )
                            v.set_id( response.id )
                            msg = 'The URI: "' +  v.getURI() + '" has a parameter named: "' + param_name
                            msg +='" with value: "' + qs[param_name][element_index] + '", which is a SQL sentence.'
                            v.set_desc( msg )
                            v.set_var( param_name )
                            v['parameterValue'] = qs[param_name][element_index]
                            v.addToHighlight(qs[param_name][element_index])
                            kb.kb.append( self , 'strange_parameters' , v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'strange_parameters', 'strange_parameters' ), 'VAR' )

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
        if 'wicket:' in parameter:
            #
            #   The wicket framework uses, by default, strange URLs like this:
            #   https://www.DOMAIN.com/?wicket:bookmarkablePage=:com.DOMAIN.SUBDOMAIN.web.pages.SignInPage
            #   &wicket:interface=:0:signInForm::IFormSubmitListener::;jsessionid=7AC76A46A86BBC3F5253E374241BC892
            #
            #   Which are strange in all cases, except from wicket!
            #
            return False

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
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps all responses and tries to identify URIs with strange
        parameters, some examples of strange parameters are:
            - http://a/?b=method(a,c)
            - http://a/?c=x|y|z|d
        '''
