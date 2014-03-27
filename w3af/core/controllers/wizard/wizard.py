"""
wizard.py

Copyright 2008 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.factory import factory


class wizard:

    def __init__(self, w3af_core):
        """
        This method should be overwritten by the actual wizards, so they can
        define what questions they are going to ask.
        """
        # Save the core
        self.w3af_core = w3af_core

        # A list of question objects
        self._question_lst = []

        # Internal variables to mantain state
        self._currentQuestion = None
        self._firstQuestion = True
        self._nextQuestionId = None
        self._already_asked = []
        self._user_options = None

    def _get_instances(self, question_list, w3af_core):
        """
        :param question_list: A list of question ids
        :param w3af_core: The w3af core object to pass to the question id
        :return: A list of question objects
        """
        res = []
        mod = 'w3af.core.controllers.wizard.questions.question_%s'
        for question_id in question_list:
            klass = mod % question_id
            question_inst = factory(klass, w3af_core)
            res.append(question_inst)
        return res

    def next(self):
        """
        The user interface calls this method until it returns None.

        :return: The next question that has to be asked to the user.
        """
        # Special case for first iteration
        if self._firstQuestion == True:
            self._firstQuestion = False
            self._currentQuestion = self._question_lst[0]
            return self._question_lst[0]

        # Save the user completed values, so we can handle previous button
        self._currentQuestion.set_previously_answered_values(self._user_options)
        self._already_asked.append(self._currentQuestion)

        # Special case to end iteration
        if self._nextQuestionId is None:
            return None

        # Find the next one
        possibleQuestions = [q for q in self._question_lst if q.get_question_id(
        ) == self._nextQuestionId]
        if len(possibleQuestions) != 1:
            raise BaseFrameworkException('We have more than one next question. Please verify your wizard definition.\
                          Possible questions are: ' + str(possibleQuestions))
        else:
            # return the next question
            self._currentQuestion = possibleQuestions[0]
            return possibleQuestions[0]

    def previous(self):
        """
        We get here when the user clicks on the "Previous" button in the GTK user interface.

        :return: The previous question, with the answers the user selected.
        """
        # Special case, we can't go back because we don't have a previous question
        if self._firstQuestion:
            return None

        # There is a list with the questions, and a list with the answers
        # We have to combine both, to return a question object that has the
        # already answered values from the user
        self._currentQuestion = self._already_asked.pop()
        return self._currentQuestion

    def get_wizard_description(self):
        """
        This method should be overwritten by the actual wizards.

        :return: A string that describes what the wizard will let you configure.
        """
        return ''

    def get_name(self):
        """
        :return: The name of the wizard.
        """
        return ''

    def set_answer(self, options_list):
        """
        Saves the answer for the current question, and finds the next question
        to be performed to the user.

        This method raises an exception if the selected options are invalid.

        :param options_list: This is a map with the answers for every question
                               that was made to the user.
        """
        # This line may rise a BaseFrameworkException
        self._nextQuestionId = self._currentQuestion.get_next_question_id(
            options_list)

        # save the options selected by the user, to be able to perform a "previous"
        self._user_options = options_list
