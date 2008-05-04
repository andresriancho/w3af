'''
session.py

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

from core.ui.consoleUi.menu import *

class sessionMenu(menu):
    '''
    Menu to control sessions.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''
    def _cmd_save(self, params):    
        if len(params) != 1:
            om.out.console("Missing parameters")
            self._help_save()
        else:
            try:
                self._w3af.saveSession(params[0])
            except Exception, e:
                om.out.console(str(e))

    
    def _cmd_resume(self, params):
        if len(params) != 1:
            om.out.console("Missing parameters")
            self._help_resume()
        else:
            try:
                self._w3af.resumeSession(params[0])
            except Exception, e:
                om.out.console(str(e))



    def _help_save(self):
        om.out.console("Usage: save <session_name>")

    def _help_resume(self):
        om.out.console("Usage: resume <session_name>")
            

       
