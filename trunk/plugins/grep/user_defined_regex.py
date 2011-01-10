'''
user_defined_regex.py

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
from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

import re


class user_defined_regex(baseGrepPlugin):
    '''
    Report a vulnerability if the respose matches a user defined regex.
      
    @author: floyd fuh ( floyd_fuh@yahoo.de )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # User defined options
        self._single_regex = ''
        self._regex_file_path = ''

        # Internal variables
        # Improved performance by compiling all the regular expressions
        # before using them (see setOptions method)
        self._regexlist_compiled = []
        self._all_in_one = None
        

    def grep(self, request, response):
        '''
        Plugin entry point, search for the user defined regex.
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if self._all_in_one is None:
            return
        
        if response.is_text_or_html():
            html_string = response.getBody()
            #Try to find one of them
            if self._all_in_one.search(html_string):
                #One of them is in there, now we need to find out which one
                for index, regex_tuple in enumerate(self._regexlist_compiled):
                    regex, info_object = regex_tuple
                    match_object = regex.search( html_string )
                    if match_object:
                        with self._plugin_lock:
                            #Don't change the next line to "if info_object:",
                            #because the info_object is an empty dict {}
                            #which evaluates to false
                            #but an info object is not the same as None
                            if not info_object is None:
                                ids = info_object.getId()
                                ids.append(response.id)
                                info_object.setId(ids)
                            else:
                                info_object = info.info()
                                info_object.setPluginName(self.getName())
                                om.out.information('User defined regular expression "'+str(regex.pattern)+'" matched a response!')
                                info_object.setURL( response.getURL() )
                                msg = 'The response matches the user defined regular expression "'+str(regex.pattern)+'":\n'
                                msg += str(match_object.group(0))
                                msg += '\n'
                                info_object.setDesc( msg )
                                info_object.setId( response.id )
                                info_object.setName( 'User defined regex - ' + str(regex.pattern) )
                                kb.kb.append( self , 'user_defined_regex' , info_object )
                            #set the info_object
                            self._regexlist_compiled[index] = (regex, info_object)
                  
    
    def setOptions( self, optionsMap ):
        '''
        Handle user configuration parameters.
        @return: None
        '''
        # The not yet compiled all_in_one_regex
        tmp_not_compiled_all = []
        #
        #   Add the regexes from the file
        #
        self._regexlist_compiled = []
        regex_file_path = optionsMap['regex_file_path'].getValue()
        if regex_file_path and not regex_file_path == 'None':
            self._regex_file_path = regex_file_path
            current_regex = ''
            try:
                f = file( self._regex_file_path)
            except:
                raise w3afException('File not found')
            else:
                for regex in f:
                    current_regex = regex.strip()
                    try:
                        self._regexlist_compiled.append((re.compile(current_regex, 
                                                                   re.IGNORECASE | re.DOTALL), None))
                        tmp_not_compiled_all.append(current_regex)
                    except:
                        f.close()
                        raise w3afException('Invalid regex in regex file: '+current_regex)
                f.close()

        #
        #   Add the single regex
        #
        self._single_regex = optionsMap['single_regex'].getValue()
        if self._single_regex and not self._single_regex == 'None':
            try:
                self._regexlist_compiled.append((re.compile(self._single_regex, 
                                                           re.IGNORECASE | re.DOTALL), None))
                tmp_not_compiled_all.append(self._single_regex)
            except:
                raise w3afException('Invalid regex in the single_regex field!')
        #
        #   Compile all in one regex
        #
        if tmp_not_compiled_all:
            # get a string like (regexA)|(regexB)|(regexC)
            all_in_one_uncompiled = '('+')|('.join(tmp_not_compiled_all)+')'
            self._all_in_one = re.compile(all_in_one_uncompiled, re.IGNORECASE | re.DOTALL)
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        optionsList = optionList()
        
        description1 = 'Single regex to use in the grep process.'
        option1 = option('single_regex', self._single_regex , description1, 'string')
        optionsList.add(option1)
        
        description2 = 'Path to file with regular expressions to use in the grep process.'
        help2 = description2 + '\n\n'
        help2 += 'Attention: The file will be loaded line by line into '
        help2 += 'memory, because the regex will be precompiled in order to achieve '
        help2 += ' better performance during the scan process. \n\n'
        help2 += 'A list of example regular expressions can be found at '
        help2 += '"plugins/grep/user_defined_regex/".'
        option2 = option('regex_file_path', self._regex_file_path , description2, 'string', help=help2)

        optionsList.add(option2)
        
        return optionsList
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        pass
            
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
        This plugin greps every response for a user defined regex.

        You can specify a single regex or an entire file of regexes (each line one regex),
        if both are specified, the single_regex will be added to the list of regular
        expressions extracted from the file.

        A list of example regular expressions can be found at "plugins/grep/user_defined_regex/".

        For every match an information message is shown.
        '''

 	  	 
