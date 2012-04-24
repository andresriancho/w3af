'''
profiles.py

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

# Import w3af
import core.controllers.w3afCore
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.consoleUi.menu import *

class profilesMenu(menu):
    '''
    Menu to control the profiles.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)

    '''
    

    def __init__(self, name, console, w3af, parent=None):
        menu.__init__(self, name, console, w3af, parent)
        self._profiles = {}
        instance_list, invalid_profiles = w3af.profiles.getProfileList()
        for profile in instance_list:
            self._profiles[profile.getName()] = profile
        self._loadHelp('profiles')


    def _cmd_use(self, params):
        '''
        @param params: A two-elems list containing the name of the profile to
            load and the original working directory.
        '''
        if not params:
            om.out.console('Parameter missing, please see the help:')
            self._cmd_help(['use'])
        else:
            profile = params[0]
            if not profile:
                raise w3afException('Unknown profile: ' + profile)
            
            try:
                workdir = params[1] 
            except IndexError:
                workdir = None            
            
            self._w3af.profiles.useProfile(profile, workdir=workdir)
            
            om.out.console('The plugins configured by the scan profile have '
                           'been enabled, and their options configured.')
            om.out.console('Please set the target URL(s) and start the scan.')

    def _cmd_list(self, params):
        if params:
            om.out.console('No parameters expected')
        else:
            table = [['Profile', 'Description'],[]]
            for profileInstance in self._profiles.values():
                table.append([profileInstance.getName() , profileInstance.getDesc()])

            self._console.drawTable(table)

    def _para_use(self, params, part):
        if not params:
            return suggest(self._profiles.keys(), part)
        return []
            
       

