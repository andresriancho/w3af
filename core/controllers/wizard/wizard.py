'''
wizard.py

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
from core.controllers.misc.factory import factory

class wizard:
    def __init__( self ):
        '''
        This method should be overwritten by the actual wizards, so they can define what questions they are
        going to ask.
        '''
        # A list of question objects
        self._questionList = []

        # Internal variables to mantain state
        self._currentQuestion = None
        self._firstQuestion = True
        self._nextQuestionId = None

    def _get_instances( self, question_list ):
        '''
        @parameter question_list: A list of question ids
        @return: A list of question objects
        '''
        res = []
        for question_id in question_list:
            res.append( factory('core.controllers.wizard.questions.question_' + question_id) )
        return res        
        
    def next(self):
        '''
        The user interface calls this method until it returns None.
        
        @return: The next question that has to be asked to the user.
        '''
        # Special case for first iteration
        if self._firstQuestion == True:
            self._firstQuestion = False
            self._currentQuestion = self._questionList[0]
            return self._questionList[0]

        # Special case to end iteration
        if self._nextQuestionId == None:
            return None

        # Find the next one
        possibleQuestions = [q for q in self._questionList if q.getQuestionId() == self._nextQuestionId ]
        if len(possibleQuestions) != 1:
            raise w3afException('We have more than one next question. Please verify your wizard definition.\
                          Possible questions are: ' + str(possibleQuestions) )
        else:
            self._currentQuestion = possibleQuestions[0]
            return possibleQuestions[0]
        
    def getWizardDescription(self):
        '''
        This method should be overwritten by the actual wizards.
        
        @return: A string that describes what the wizard will let you configure.
        '''
        return ''

    def getName(self):
        '''
        @return: The name of the wizard.
        '''
        return ''
        
    def setAnswer(self, optionsMap):
        '''
        Saves the answer for the current question, and finds the next question to be performed to the user.

        This method raises an exception if the selected options are invalid.
        
        @parameter optionsMap: This is a map with the answers for every question that was made to the user.
        '''
        self._nextQuestionId = self._currentQuestion.getNextQuestionId( optionsMap )
        
