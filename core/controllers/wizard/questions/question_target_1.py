'''
question_target_1.py

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

class question_target_1(question):
    '''
    This is the first question of the wizard, where you have to speficy the target.
    '''
    def __init__(self):
        self._questionId = 'target_1'
        
        self._questionString = 'In this step you should specify the target URL for the framework.'
        self._questionString += ' Remember that you can use the file:// handler to speficy a list '
        self._questionString += ' of target URLs to scan for vulnerabilities.'
        
    def getAnswerObjects(self):
        '''
        @return: A list of options for this question.
        '''
        d1 = 'Target URL'
        o1 = option('Target URL', '', d1, 'string')
        
        ol.add(o1)
        return ol
        
    def setAnswer(self,  optionsMap ):
        self._answers = optionsMap
        
        target = optionsMap['Target URL'].getValue()
        if not target:
            raise w3afException('You can not leave the "Target URL" parameter unconfigured.')

    def getNextQuestionId(self,  optionsMap ):
        return 'target_2'

