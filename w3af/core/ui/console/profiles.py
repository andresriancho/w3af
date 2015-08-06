"""
profiles.py

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
import w3af.core.controllers.output_manager as om

from w3af.core.ui.console.menu import menu
from w3af.core.ui.console.util import suggest
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.profile.profile import profile as Profile


class ProfilesMenu(menu):
    """
    Menu to control the profiles.
    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)

    """

    def __init__(self, name, console, w3af, parent=None):
        menu.__init__(self, name, console, w3af, parent)
        self._profiles = {}
        instance_list, invalid_profiles = w3af.profiles.get_profile_list()
        for _profile in instance_list:
            self._profiles[_profile.get_name()] = _profile
        self._load_help('profiles')

    def _cmd_use(self, params):
        """
        :param params: A two-elems list containing the name of the profile to
                       load and the original working directory.
        """
        if not params:
            om.out.console('Parameter missing, please see the help:')
            self._cmd_help(['use'])
        else:
            profile = params[0]

            try:
                workdir = params[1]
            except IndexError:
                workdir = None

            try:
                self._w3af.profiles.use_profile(profile, workdir=workdir)
            except BaseFrameworkException, w3:
                om.out.console(str(w3))

            om.out.console('The plugins configured by the scan profile have '
                           'been enabled, and their options configured.')
            om.out.console('Please set the target URL(s) and start the scan.')

    def _cmd_list(self, params):
        if params:
            om.out.console('No parameters expected')
        else:
            table = [['Profile', 'Description'], []]
            for profileInstance in self._profiles.values():
                table.append(
                    [profileInstance.get_name(), profileInstance.get_desc()])

            self._console.draw_table(table)

    def _cmd_save_as(self, params):
        """
        Saves the current config to a new profile.
        """
        self_contained = False

        if not params:
            om.out.console('Parameter missing, please see the help:')
            self._cmd_help(['save_as'])
            return

        elif len(params) == 1:
            # This is the most common case where the user just specifies a
            # profile name to save
            profile_name = params[0]

        elif len(params) == 2:
            # This is the case to support self contained profiles
            # https://github.com/andresriancho/w3af/issues/10949
            profile_name = params[0]
            self_contained = params[1]

            if 'self-contained' != self_contained:
                om.out.console('Invalid profile save flag, please see the help:')
                self._cmd_help(['save_as'])
                return
            else:
                self_contained = True

        else:
            om.out.console('Too many parameters, please see the help:')
            self._cmd_help(['save_as'])
            return

        # Validate the profile name
        try:
            Profile.is_valid_profile_name(profile_name)
        except BaseFrameworkException, bfe:
            om.out.console('%s' % bfe)
            return

        description = 'Profile generated using the console UI.'
        self._w3af.profiles.save_current_to_new_profile(profile_name,
                                                        description,
                                                        self_contained=self_contained)
        
        om.out.console('Profile saved.')

    def _para_use(self, params, part):
        if not params:
            return suggest(self._profiles.keys(), part)
        return []

    _para_save_as = _para_use
