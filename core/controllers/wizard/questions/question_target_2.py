'''
question_target_2.py

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

class question_target_2(question):
    '''
    This is the first question of the wizard, where you have to speficy the target.
    '''
    def __init__(self):
        self._questionId = 'target_2'

        self._questionTitle = 'Target Location'
        
        self._questionString = 'w3af has a group of plugins that fetch information about your target application'
        self._questionString += ' using Internet search engines. In order to enable or disable those plugins, we need'
        self._questionString += ' to know the following:'

        
    def getOptionObjects(self):
        '''
        @return: A list of options for this question.
        '''

        d1 = 'Is your web application reachable from the Internet?'
        o1 = option('internet',True, d1, 'boolean')

        ol = optionList()
        ol.add(o1)

        return ol
        
    def getNextQuestionId(self,  optionsMap ):

        internet = optionsMap['internet'].getValue()
        # FIXME: Do something with this value

        return None


