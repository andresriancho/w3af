"""
question.py

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
from w3af.core.data.options.option_list import OptionList


class question(object):
    """
    This class represents a question that is made to a user through a wizard.

    The idea is that a wizard object has a lot of this question objects.
    """
    def __init__(self, w3af_core):
        self._question_id = ''
        self._question_str = ''
        self.w3af_core = w3af_core

        self._previously_answered_values = None

    def get_question_title(self):
        return self._question_title

    def set_question_title(self, s):
        self._question_title = s

    def get_question_string(self):
        return self._question_str

    def set_question_string(self, s):
        self._question_str = s

    def get_option_objects(self):
        """
        This is the method that is shown to the user interfaces;
        while the real information is inside the _get_option_objects().

        :return: A list of options for this question.
        """
        if self._previously_answered_values:
            # We get here when the user hits previous
            return self._previously_answered_values
        else:
            return self._get_option_objects()

    def _get_option_objects(self):
        """
        We get here when the user wants to complete this step of the
        wizard, and he didn't pressed Previous.

        :return: The option objects
        """
        ol = OptionList()
        return ol

    def set_previously_answered_values(self, values):
        """
        This is needed to implement the previous/back feature!
        """
        self._previously_answered_values = values

    def get_question_id(self):
        return self._question_id

    def set_question_id(self, qid):
        self._question_id = qid

    def get_next_question_id(self, options_list):
        """
        :return: The id of the next question that the wizard has to ask to the
                 user, based on the options_list. None if this is the last
                 question of the wizard.
        """
        return None

    def __repr__(self):
        return '<question object ' + self._question_id + '>'
