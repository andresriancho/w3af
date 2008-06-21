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

class wizard:
    def __init__( self ):
        '''
        This method should be overwritten by the actual wizards, so they can define what questions they are
        going to ask.
        '''
        self._questionList = []
        self._currentQuestion = None
        self._firstQuestion = None
        self._nextQuestionId = ''
        
    def getnext(self):
        '''
        The user interface calls this method until it returns None.
        
        @return: The next question that has to be asked to the user.
        '''
        _nextQuestionId = self._currentQuestion.getNextQuestionId()
        
        possibleQuestions = [q for q in self._questionList if q.getQuestionId() == _nextQuestionId ]
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
        
    def setAnswer(self,  optionsMap):
        '''
        Saves the answer for the current question, and finds the next question to be performed to the user.
        
        @parameter optionsMap: This is a map with the answers for every question that was made to the user.
        '''
        self._currentQuestion.setAnswer( answerList )
        
