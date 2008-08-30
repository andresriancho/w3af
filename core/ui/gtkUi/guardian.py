'''
guardian.py

Copyright 2007 Andres Riancho

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

import gtk, gobject
from . import helpers
import core.data.kb.knowledgeBase as kb
import core.data.kb
        

class _Guarded(object):
    '''Helper for the guardian.'''
    def __init__(self, objtype):
        self.icon = helpers.KB_ICONS[objtype, None]
        self._quant = 0
        self.label = gtk.Label("0".ljust(5))

    def _qset(self, newval):
        self._quant = newval
        self.label.set_text(str(newval).ljust(5))
    quant = property(lambda s: s._quant, _qset)
        

class FoundObjectsGuardian(gtk.HBox):
    '''Shows the objects found by the core.

    @param w3af: the core

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(FoundObjectsGuardian,self).__init__()
        self.w3af = w3af
    
        # tooltip
        self.set_tooltip_text("Amount of discovered vulnerabilities and generated shells")
    
        # what to show
        self.info = _Guarded("info")
        self.vuln = _Guarded("vuln")
        self.shll = _Guarded("shell")
        self.objcont = {
            core.data.kb.vuln.vuln: self.vuln,
            core.data.kb.info.info: self.info,
        }

        # builds the presentation
        self.pack_start(self.info.icon, False, False, padding=2)
        self.pack_start(self.info.label, False, False, padding=2)
        self.pack_start(self.vuln.icon, False, False, padding=2)
        self.pack_start(self.vuln.label, False, False, padding=2)
        self.pack_start(self.shll.icon, False, False, padding=2)
        self.pack_start(self.shll.label, False, False, padding=2)

        # go live
        self.fullkb = kb.kb.dump()
        self.kbholder = set()
        gobject.timeout_add(1000, self._update)
        self.show_all()

    def _update(self):
        '''Updates the objects shown.'''
        # shells
        shells = kb.kb.getAllShells()
        self.shll.quant = len(shells)

        # infos
        infos = kb.kb.getAllInfos()
        self.info.quant = len(infos)

        # vulns
        vulns = kb.kb.getAllVulns()
        self.vuln.quant = len(vulns)
        return True

