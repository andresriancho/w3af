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
    def __init__( self, w3af_core ):
        '''
        This method should be overwritten by the actual wizards, so they can define what questions they are
        going to ask.
        '''
        # Save the core
        self.w3af_core = w3af_core
        
        # A list of question objects
        self._questionList = []

        # Internal variables to mantain state
        self._currentQuestion = None
        self._firstQuestion = True
        self._nextQuestionId = None
        self._already_asked = []
        self._user_options = None

    def _get_instances( self, question_list ):
        '''
        @parameter question_list: A list of question ids
        @return: A list of question objects
        '''
        res = []
        for question_id in question_list:
            question_instance = factory('core.controllers.wizard.questions.question_' + question_id)
            question_instance.w3af_core = self.w3af_core
            res.append( question_instance )
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

        # Save the user completed values, so we can handle previous button of the wizard
        self._currentQuestion.setPreviouslyAnsweredValues(self._user_options)
        self._already_asked.append( self._currentQuestion )

        # Special case to end iteration
        if self._nextQuestionId is None:
            return None

        # Find the next one
        possibleQuestions = [q for q in self._questionList if q.getQuestionId() == self._nextQuestionId ]
        if len(possibleQuestions) != 1:
            raise w3afException('We have more than one next question. Please verify your wizard definition.\
                          Possible questions are: ' + str(possibleQuestions) )
        else:
            # return the next question
            self._currentQuestion = possibleQuestions[0]
            return possibleQuestions[0]

    def previous(self):
        '''
        We get here when the user clicks on the "Previous" button in the GTK user interface.

        @return: The previous question, with the answers the user selected.
        '''
        # Special case, we can't go back because we don't have a previous question
        if self._firstQuestion:
            return None

        # There is a list with the questions, and a list with the answers
        # We have to combine both, to return a question object that has the
        # already answered values from the user
        self._currentQuestion = self._already_asked.pop()
        return self._currentQuestion
        
        
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
        # This line may rise a w3afException        
        self._nextQuestionId = self._currentQuestion.getNextQuestionId( optionsMap )
        
        # save the options selected by the user, to be able to perform a "previous"
        self._user_options = optionsMap
