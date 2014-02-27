"""
kb_add_wizard.py

Copyright 2013 Andres Riancho

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

from w3af.core.ui.gui.confpanel import ConfigDialog
from w3af.core.data.kb.vuln_templates.utils import (get_template_names,
                                               get_template_by_name)


class KBAddWizard(object):
    
    def __init__(self):
        pass
    
    def start_wizard(self):
        """
        get_template_names()
        
        template = get_template_by_name(chosen_template)
        ConfigDialog(_("Vulnerability settings"), self.w3af, template)
        """
        pass