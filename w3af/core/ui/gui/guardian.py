"""
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
"""
import gtk
import gobject

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.kb

from w3af.core.ui.gui import helpers
from w3af.core.ui.gui.exception_handling import handled

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.shell import Shell
from w3af.core.data.kb.kb_observer import KBObserver
from w3af.core.data.constants.severity import INFORMATION, MEDIUM, HIGH, LOW


class _Guarded(object):
    """Helper for the guardian."""
    def __init__(self, objtype):
        self.icon = helpers.KB_ICONS[objtype, None]
        self.quant = 0
        self.label = gtk.Label("0".ljust(5))

    def inc(self):
        self.quant += 1
        gobject.idle_add(self.update_label)
    
    def update_label(self):
        self.label.set_text(str(self.quant).ljust(5))
        return False


class FoundObjectsGuardian(gtk.HBox):

    def __init__(self, _w3af):
        """Shows the objects found by the core.

        :param w3af: the core

        :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
        """
        super(FoundObjectsGuardian, self).__init__()
        self.w3af = _w3af

        # tooltip
        self.set_tooltip_text(
            _("Amount of discovered vulnerabilities and generated shells"))

        # what to show
        self.info = _Guarded("info")
        self.vuln = _Guarded("vuln")
        self.shll = _Guarded("shell")
        self.objcont = {
            w3af.core.data.kb.vuln: self.vuln,
            w3af.core.data.kb.info: self.info,
        }

        # builds the presentation
        self.pack_start(self.info.icon, False, False, padding=2)
        self.pack_start(self.info.label, False, False, padding=2)
        self.pack_start(self.vuln.icon, False, False, padding=2)
        self.pack_start(self.vuln.label, False, False, padding=2)
        self.pack_start(self.shll.icon, False, False, padding=2)
        self.pack_start(self.shll.label, False, False, padding=2)

        # go live
        kb.kb.add_observer(VulnerabilityCountObserver(self))
        self.show_all()


class VulnerabilityCountObserver(KBObserver):
    def __init__(self, found_count_guardian):
        self.found_count_guardian = found_count_guardian

    def append(self, location_a, location_b, value, ignore_type=False):
        """
        Updates the object count shown.

        Called by the knowledge base when a new item is added to it.
        """
        if isinstance(value, Shell):
            self.found_count_guardian.shll.inc()

        elif hasattr(value, 'get_severity'):
            if value.get_severity() in (LOW, MEDIUM, HIGH):
                self.found_count_guardian.vuln.inc()

            elif value.get_severity() == INFORMATION:
                self.found_count_guardian.info.inc()


class FoundExceptionsStatusBar(gtk.EventBox):
    """
    Shows the number of exceptions found during the scan in the status bar

    :author: Andres Riancho <andres.riancho =at= gmail.com>
    """
    def __init__(self, w3af):
        super(FoundExceptionsStatusBar, self).__init__()
        self.w3af = w3af

        self.hbox = gtk.HBox()

        self.set_tooltip_text(_("Exceptions raised during the scan"))

        self.exceptions = _Guarded("excp")
        self.hbox.pack_start(self.exceptions.icon, False, False, padding=2)
        self.hbox.pack_start(self.exceptions.label, False, False, padding=2)

        self.add(self.hbox)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

        self.connect("button-press-event", self._report_bug)

    def show_all(self, num):
        """Updates the object and shows all."""
        self.exceptions.inc()
        super(FoundExceptionsStatusBar, self).show_all()

    def _report_bug(self, widg, evt):
        """User clicked on me, he wants to report a bug"""
        handled.handle_exceptions(self.w3af)
        # TODO: Hide this status bar if and only if the user DID report
        # the exceptions to Github
