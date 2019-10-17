"""
wizard.py

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
import gtk
import os
import cgi

from w3af import ROOT_PATH
from w3af.core.ui.gui import GUI_DATA_PATH
from w3af.core.ui.gui import entries, confpanel, helpers
from w3af.core.controllers.exceptions import BaseFrameworkException


class Quest(object):
    def __init__(self, quest):
        self.quest = quest
        self.ptype = self.pname = None

    def get_options(self):
        opts = self.quest.get_option_objects()
        return opts


class QuestOptions(gtk.VBox):
    def __init__(self, w3af, wizard):
        self.w3af = w3af
        self.wizard = wizard
        super(QuestOptions, self).__init__()

        self.widg = gtk.Label("")
        self.pack_start(self.widg)
        self.activeQuestion = None

        self.show_all()

    def save_options(self):
        """Saves the changed options."""
        options = self.widg.options
        invalid = []

        for opt in options:
            #       Trying to reproduce bug
            #       https://sourceforge.net/tracker2/?func=detail&aid=2652434&group_id=170274&atid=853652
            #
            #       To get more info:
            try:
                opt.widg
            except Exception as e:
                raise Exception(str(e) + ' || ' + opt.get_name())
            # end of debugging code

            if hasattr(opt.widg, "is_valid"):
                if not opt.widg.is_valid():
                    invalid.append(opt.get_name())
        if invalid:
            msg = "The configuration can't be saved, there is a problem in the"
            msg += " following parameter(s):\n\n" + "\n-".join(invalid)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title('Configuration error')
            dlg.run()
            dlg.destroy()
            return

        for opt in options:
            opt.set_value(opt.widg.get_value())

        try:
            helpers.coreWrap(self.wizard.set_answer, options)
        except BaseFrameworkException:
            return
        return True

    def config_changed(self, flag):
        # just to comply with API
        pass

    def set_quest_options(self, quest):
        self.activeQuestion = quest
        self.remove(self.widg)
        self.widg = confpanel.OnlyOptions(
            self, self.w3af, Quest(quest), gtk.Button(), gtk.Button())
        self.pack_start(self.widg)

    def ask_final(self):
        # the text entries
        table = gtk.Table(2, 2)
        for row, tit in enumerate(("Name", "Description")):
            titlab = gtk.Label(tit)
            titlab.set_alignment(0.0, 0.5)
            table.attach(titlab, 0, 1, row, row + 1)
            entry = gtk.Entry()
            table.attach(entry, 1, 2, row, row + 1)
        table.show_all()
        # insert it
        self.remove(self.widg)
        self.widg = table
        self.pack_start(self.widg)


class Wizard(entries.RememberingWindow):
    """The wizard to help the user to create a profile.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """

    def __init__(self, w3af, wizard):
        super(Wizard, self).__init__(
            w3af, "wizard", "w3af Wizard: " + wizard.get_name(), "Wizards",
            guessResize=False)
        self.w3af = w3af
        self.wizard = wizard

        # the image at the left
        mainhbox = gtk.HBox()
        self.vbox.pack_start(mainhbox)
        leftframe = gtk.image_new_from_file(os.path.join(GUI_DATA_PATH,
                                                         'wizard_frame.png'))
        mainhbox.pack_start(leftframe, False, False)
        mainvbox = gtk.VBox()
        mainhbox.pack_start(mainvbox)

        # the structure
        self.qtitle = gtk.Label()
        mainvbox.pack_start(self.qtitle, False, False, padding=10)
        self.quest = gtk.Label()
        self.quest.set_line_wrap(True)
        mainvbox.pack_start(self.quest, True, False, padding=10)
        self.panel = QuestOptions(w3af, wizard)
        mainvbox.pack_start(self.panel, True, False, padding=10)

        # fill it
        self.nextbtn = gtk.Button("  Next  ")
        quest = self.wizard.next()

        self._firstQuestion = quest
        self._buildWindow(quest)

        # go button
        butbox = gtk.HBox()
        self.prevbtn = gtk.Button("  Back  ")
        self.prevbtn.set_sensitive(False)
        self.prevbtn.connect("clicked", self._goBack)
        butbox.pack_start(self.prevbtn, True, False)
        self.nextbtn.connect("clicked", self._goNext)
        butbox.pack_start(self.nextbtn, True, False)
        mainvbox.pack_start(butbox, False, False)

        # Show all!
        self.finalQ = False
        self.show_all()

    def _saveEverything(self):
        """Saves all the info to a profile."""
        filename = self.panel.widg.get_children()[2].get_text()
        description = self.panel.widg.get_children()[0].get_text()
        if not filename:
            msg = "The configuration can't be saved, you need to insert a profile name!\n\n"
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title('Missing info')
            dlg.run()
            dlg.destroy()
            return

        filename = cgi.escape(filename)
        try:
            helpers.coreWrap(self.w3af.profiles.save_current_to_new_profile,
                             filename, description)
        except BaseFrameworkException:
            self.w3af.mainwin.sb(_("There was a problem saving the profile!"))
            return
        self.w3af.mainwin.profiles.load_profiles(filename)
        self.w3af.mainwin.sb(_("New profile created"))
        self.destroy()

    def _goNext(self, widg):
        """Shows the next question."""
        if self.finalQ:
            self._saveEverything()
            return
        if not self.panel.save_options():
            return
        quest = self.wizard.next()
        self.prevbtn.set_sensitive(True)
        if quest is None:
            self._buildFinal()
        else:
            self._buildWindow(quest)

    def _goBack(self, widg):
        """Shows the previous question."""
        if not self.finalQ:
            if not self.panel.save_options():
                return
        self.finalQ = False
        quest = self.wizard.previous()
        if quest is self._firstQuestion:
            self.prevbtn.set_sensitive(False)
        self._buildWindow(quest)

    def _buildWindow(self, question):
        """Builds the useful pane for a question.

        :param question: the question with the info to build.
        """
        self.qtitle.set_markup("<b>%s</b>" % question.get_question_title())
        self.quest.set_text(question.get_question_string())
        self.panel.set_quest_options(question)
        self.nextbtn.set_label("  Next  ")
        self.finalQ = False

    def _buildFinal(self):
        """End titles window."""
        self.qtitle.set_markup("<b>The wizard has finished</b>")
        self.quest.set_text(
            "There are no more questions, you correctly created a new "
            "configuration for w3af.\n\nPlease provide a name and a "
            "description for the new profile:")
        self.panel.ask_final()
        self.nextbtn.set_label("  Save  ")
        self.finalQ = True


class SimpleRadioButton(gtk.VBox):
    """Simple to use radiobutton."""

    def __init__(self, callback):
        super(SimpleRadioButton, self).__init__()
        self.selected = None
        self._rb = None
        self.callback = callback
        self.active = None

    def add(self, text, obj):
        self._rb = gtk.RadioButton(self._rb, text)
        self._rb.connect("toggled", self._changed, obj)
        self.pack_start(self._rb, False, False)
        if self.active is None:
            self.active = obj

    def _changed(self, widget, obj):
        if widget.get_active():
            self.callback(obj)
            self.active = obj


class WizardChooser(entries.RememberingWindow):
    """Window that let's the user to choose a Wizard.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """

    def __init__(self, w3af):
        super(WizardChooser, self).__init__(
            w3af, "wizardchooser", "w3af - Wizard Chooser", "Wizards",
            guessResize=False)
        self.w3af = w3af

        # the image at the left
        mainhbox = gtk.HBox()
        self.vbox.pack_start(mainhbox)
        leftframe = gtk.image_new_from_file(os.path.join(GUI_DATA_PATH,
                                                         'wizard_frame.png'))
        vb = gtk.VBox()
        vb.pack_end(leftframe, False, False)
        eb = gtk.EventBox()
        eb.add(vb)
        color = gtk.gdk.color_parse('#FFFFFF')
        eb.modify_bg(gtk.STATE_NORMAL, color)
        mainhbox.pack_start(eb, False, False)
        mainvbox = gtk.VBox()
        mainhbox.pack_start(mainvbox)

        # the message
        l = gtk.Label("Select the wizard to run:")
        mainvbox.pack_start(l, False, False, padding=10)

        # radiobutton and descrip
        innerbox = gtk.HBox()
        self.rbuts = SimpleRadioButton(self._changedRB)
        initlabel = None
        for wiz in self._getWizards():
            if initlabel is None:
                initlabel = wiz.get_wizard_description()
            self.rbuts.add(wiz.get_name(), wiz)
        innerbox.pack_start(self.rbuts, True, False)

        self.wizdesc = gtk.Label(initlabel)
        innerbox.pack_start(self.wizdesc, padding=10)
        mainvbox.pack_start(innerbox, True, False)

        # go button
        buthbox = gtk.HBox()
        gobtn = gtk.Button("Run the wizard")
        gobtn.connect("clicked", self._goWizard)
        buthbox.pack_start(gobtn, True, False)
        mainvbox.pack_start(buthbox, False, False, padding=10)

        # Show all!
        self.show_all()

    def _changedRB(self, widget):
        """The radiobutton changed."""
        self.wizdesc.set_label(widget.get_wizard_description())

    def _goWizard(self, widget):
        """Runs the selected wizard."""
        # First, clean all the enabled plugins that the user may have selected:
        for ptype in self.w3af.plugins.get_plugin_types():
            self.w3af.plugins.set_plugins([], ptype)

        # Destroy myself
        self.destroy()

        # Run the selected wizard
        Wizard(self.w3af, self.rbuts.active)

    def _getWizards(self):
        """Returns the existing wizards."""
        wizs = []
        wizard_path = os.path.join(
            ROOT_PATH, 'core/controllers/wizard/wizards')

        for arch in os.listdir(wizard_path):
            if arch.endswith(".py") and not arch.startswith("__"):
                base = arch[:-3]
                modbase = __import__("w3af.core.controllers.wizard.wizards." +
                                     base, fromlist=[None])
                cls = getattr(modbase, base)
                wizard_instance = cls(self.w3af)
                wizs.append(wizard_instance)
        return wizs
