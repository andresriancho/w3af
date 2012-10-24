'''
gnome.py

Copyright 2011 Andres Riancho

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
import os

from core.ui.gtkUi.tests.ldtp_wrapper.xvfb_server import XVFBServer 


class Gnome(object):
    '''
    This class runs all the required commands to have a working Gnome
    environment within a Xvfb; which is required to be able to have a11y
    features, which are needed for LDTP to work.
    
    Lots of tricks seen in this code were taken from mago's documentation
    on how to run Mago on Hudson and from dogtail's run headless script:
    
        * http://mago.ubuntu.com/Documentation/RunningOnHudson
        * https://fedorahosted.org/dogtail/browser/scripts/dogtail-run-headless?rev=099577f6152ebd229eae530fff6b2221f72f05ae
    '''

    TRUE='true'
    FALSE='false'
    A11Y_GCONF_KEY = '/desktop/gnome/interface/accessibility'
    
    def get_gconf_value(self, key):
        cmd = 'gconftool-2 --get ' + key
        answer = os.popen(cmd).readlines()[0].strip()
        if answer == self.TRUE: return True
        elif answer == self.FALSE: return False
        else: raise RuntimeError, answer
    
    def set_gconf_value(self, key, value):
        if value == True: value = self.TRUE
        elif value == False: value = self.FALSE
        else: raise TypeError, value
        cmd = 'gconftool-2 --type bool --set %s %s' % (key, value)
        os.popen(cmd)
    
    