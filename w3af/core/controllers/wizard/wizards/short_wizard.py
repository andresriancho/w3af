"""
short_wizard.py

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
from w3af.core.controllers.wizard.wizard import wizard


class short_wizard(wizard):

    def __init__(self, w3af_core):
        """
        This method should be overwritten by the actual wizards, so they can
        define what questions they are going to ask.
        """
        wizard.__init__(self, w3af_core)

        self._question_lst = self._get_instances(['target_1', 'target_2'],
                                                 w3af_core)

    def get_wizard_description(self):
        """
        This method should be overwritten by the actual wizards.

        :return: A string that describes what the wizard will let you configure.
        """
        return 'This is a small demo wizard to be able to code the GUI'

    def get_name(self):
        """
        :return: The name of the wizard.
        """
        return 'Short wizard'
