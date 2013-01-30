'''
guardian.py

Copyright 2007 Andres Riancho

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
'''
import gtk
import gobject
import core.data.kb.knowledge_base as kb
import core.data.kb

from core.ui.gui import helpers

from core.ui.gui.exception_handling import handled


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
        super(FoundObjectsGuardian, self).__init__()
        self.w3af = w3af

        # tooltip
        self.set_tooltip_text(
            _("Amount of discovered vulnerabilities and generated shells"))

        # what to show
        self.info = _Guarded("info")
        self.vuln = _Guarded("vuln")
        self.shll = _Guarded("shell")
        self.objcont = {
            core.data.kb.vuln: self.vuln,
            core.data.kb.info: self.info,
        }

        # builds the presentation
        self.pack_start(self.info.icon, False, False, padding=2)
        self.pack_start(self.info.label, False, False, padding=2)
        self.pack_start(self.vuln.icon, False, False, padding=2)
        self.pack_start(self.vuln.label, False, False, padding=2)
        self.pack_start(self.shll.icon, False, False, padding=2)
        self.pack_start(self.shll.label, False, False, padding=2)

        # go live
        gobject.timeout_add(300, self._update)
        self.show_all()

    def _update(self):
        '''Updates the objects shown.'''
        # shells
        shells = kb.kb.get_all_shells()
        self.shll.quant = len(shells)
        yield True
        
        # infos
        infos = kb.kb.get_all_infos()
        self.info.quant = len(infos)
        yield True
        
        # vulns
        vulns = kb.kb.get_all_vulns()
        self.vuln.quant = len(vulns)
        yield True


class FoundExceptionsStatusBar(gtk.EventBox):
    '''
    Shows the number of exceptions found during the scan in the status bar

    @author: Andres Riancho <andres.riancho =at= gmail.com>
    '''
    def __init__(self, w3af):
        super(FoundExceptionsStatusBar, self).__init__()
        self.w3af = w3af

        self.hbox = gtk.HBox()

        self.set_tooltip_text(_("Exceptions were raised during the scan"))

        self.exceptions = _Guarded("excp")
        self.hbox.pack_start(self.exceptions.icon, False, False, padding=2)
        self.hbox.pack_start(self.exceptions.label, False, False, padding=2)

        self.add(self.hbox)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

        self.connect("button-press-event", self._report_bug)

    def show_all(self, num):
        '''Updates the object and shows all.'''
        self.exceptions.quant = num
        super(FoundExceptionsStatusBar, self).show_all()

    def _report_bug(self, widg, evt):
        '''User clicked on me, he wants to report a bug'''
        handled.handle_exceptions(self.w3af)
        # TODO: Hide this status bar if and only if the user DID report
        # the exceptions to Trac
