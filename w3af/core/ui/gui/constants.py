"""
constants.py

Copyright 2012 Andres Riancho

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
import os

from w3af.core.ui.gui import GUI_DATA_PATH


W3AF_ICON = os.path.join(GUI_DATA_PATH, 'w3af_icon.png')

MAIN_TITLE = "w3af - Web Application Attack and Audit Framework"

UI_MENU = """
<ui>
  <menubar name="MenuBar">
    <menu action="ProfilesMenu">
      <menuitem action="New"/>
      <menuitem action="Save"/>
      <menuitem action="SaveAs"/>
      <menuitem action="Revert"/>
      <menuitem action="Delete"/>
      <menuitem action="Quit"/>
    </menu>
    <menu action="EditMenuScan">
      <menuitem action="EditPlugin"/>
    </menu>
    <menu action="ViewMenuExploit">
      <menuitem action="ExploitVuln"/>
      <menuitem action="Interactive"/>
    </menu>
    <menu action="ToolsMenu">
      <menuitem action="ManualRequest"/>
      <menuitem action="FuzzyRequest"/>
      <menuitem action="EncodeDecode"/>
      <menuitem action="ExportRequest"/>
      <menuitem action="Compare"/>
      <menuitem action="Proxy"/>
    </menu>
    <menu action="ConfigurationMenu">
      <menuitem action="URLconfig"/>
      <menuitem action="Miscellaneous"/>
    </menu>
    <menu action="HelpMenu">
      <menuitem action="Help"/>
      <menuitem action="Wizards"/>
      <menuitem action="ReportBug"/>
      <separator name="s4"/>
      <menuitem action="About"/>
    </menu>
  </menubar>
  <toolbar name="Toolbar">
    <toolitem action="Wizards"/>
    <separator name="s5"/>
    <toolitem action="New"/>
    <toolitem action="Save"/>
    <separator name="s1"/>
    <toolitem action="StartStop"/>
    <toolitem action="Pause"/>
    <separator name="s2"/>
    <toolitem action="ExploitAll"/>
    <separator name="s3"/>
    <toolitem action="ManualRequest"/>
    <toolitem action="FuzzyRequest"/>
    <toolitem action="EncodeDecode"/>
    <toolitem action="ExportRequest"/>
    <toolitem action="Compare"/>
    <toolitem action="Proxy"/>
  </toolbar>
</ui>
"""
