'''
question.py

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

class question:
    '''
    This class represents a question that is made to a user through a wizard.
    
    The idea is that a wizard object has a lot of this question objects.
    '''
    def __init__(self):
        self._questionId = ''
        self._questionString = ''
        self.w3af_core = None

        self._previously_answered_values = None

    def getQuestionTitle(self):
        return self._questionTitle
        
    def setQuestionTitle(self, s):
        self._questionTitle = s    

    def getQuestionString(self):
        return self._questionString
        
    def setQuestionString(self, s):
        self._questionString = s
        
    def getOptionObjects(self):
        '''
        This is the method that is shown to the user interfaces;
        while the real information is inside the _getOptionObjects().

        @return: A list of options for this question.
        '''
        if self._previously_answered_values:
            # We get here when the user hits previous
            return self._previously_answered_values
        else:
            return self._getOptionObjects()

    def _getOptionObjects(self):
        '''
        We get here when the user wants to complete this step of the
        wizard, and he didn't pressed Previous.

        @return: The option objects
        '''
        ol = optionList()
        return ol
    
    def setPreviouslyAnsweredValues(self, values):
        '''
        This is needed to implement the previous feature!
        '''
        self._previously_answered_values = values

    def getQuestionId(self):
        return self._questionId
        
    def setQuestionId(self, qid):
        self._questionId = qid
        
    def getNextQuestionId(self, optionsMap):
        '''
        @return: The id of the next question that the wizard has to ask to the user, based on the optionsMap.
                 None if this is the last question of the wizard.
        '''
        return None
        
    def __repr__(self):
        return '<question object '+self._questionId+'>'
        
