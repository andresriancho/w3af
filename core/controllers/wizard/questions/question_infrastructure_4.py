'''
question_infrastructure_4.py

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

# Import the core singleton
from core.controllers.w3afCore import wCore as w3af_core
import core.data.kb.config as cf


class question_infrastructure_4(question):
    '''
    This is the first question of the wizard, where you have to speficy the target.
    '''
    def __init__(self):
        question.__init__( self )
    
        self._questionId = 'infrastructure_4'

        self._questionTitle = 'Plugin selection'
        
        self._questionString = 'w3af has a group of plugins that fetch information about the target'
        self._questionString += ' application using Internet search engines. In order to enable or'
        self._questionString += ' disable those plugins, we need to know the following:'
        
    def _getOptionObjects(self):
        '''
        @return: A list of options for this question.
        '''

        self._d1 = 'Is the target web application reachable from the Internet?'
        o1 = option(self._d1, True, self._d1, 'boolean')
    
        ol = optionList()
        ol.add(o1)

        return ol
        
    def getNextQuestionId(self,  optionsMap ):
        cf.cf.save('reachable_from_internet', optionsMap[self._d1].getValue())
       
       # The next question
        if cf.cf.getData('reachable_from_internet'):
            return 'infrastructure_internet_1'
        else:
            return None
