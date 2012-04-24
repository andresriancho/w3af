'''
question_infrastructure_3.py

Copyright 2008 Andres Riancho

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

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.wizard.question import question


class question_infrastructure_3(question):
    '''
    This is the first question of the wizard, where you have to speficy the target.
    '''
    def __init__(self):
        question.__init__( self )
    
        self._questionId = 'infrastructure_3'

        self._questionTitle = 'Plugin selection'
        
        self._questionString = 'This step allows you to select from a group of plugins that'
        self._questionString += ' fingerprint the remote Web server.'
        
    def _getOptionObjects(self):
        '''
        @return: A list of options for this question.
        '''
        self._d1 = 'Identify Operating System'
        o1 = option( self._d1, True, self._d1, 'boolean')
        
        self._d2 = 'Fingerprint Web Server vendor and version'
        o2 = option(self._d2, True, self._d2, 'boolean')
        
        self._d3 = 'Fingerprint programming framework'
        o3 = option(self._d3, True, self._d3, 'boolean')
        
        self._d4 = 'Find virtual hosts'
        o4 = option(self._d4, True, self._d4, 'boolean')
    
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)

        return ol
        
    def getNextQuestionId(self,  optionsMap ):
        plugin_list = []
        
        if optionsMap[self._d1].getValue():
            plugin_list.append('fingerprint_os')
            
        if optionsMap[self._d2].getValue():
            plugin_list.append('hmap')
            plugin_list.append('serverHeader')
            
        if optionsMap[self._d3].getValue():
            plugin_list.append('phpEggs')
            plugin_list.append('dotNetErrors')
            
        if optionsMap[self._d4].getValue():
            plugin_list.append('findvhost')
        
        # Set the plugins to be run
        old_discovery = self.w3af_core.plugins.getEnabledPlugins( 'discovery' )
        plugin_list.extend(old_discovery)
        self.w3af_core.plugins.setPlugins( plugin_list, 'discovery' )
        
        # Next question
        return 'infrastructure_4'
