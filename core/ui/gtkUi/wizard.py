'''
wizard.py

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

import gtk, os, cgi
from . import entries, confpanel, helpers
from core.controllers.w3afException import w3afException


class Quest(object):
    def __init__(self, quest):
        self.quest = quest
        self.ptype = self.pname = None

    def getOptions(self):
        opts = self.quest.getOptionObjects()
        return opts

class QuestOptions(gtk.VBox):
    def __init__(self, w3af, wizard):
        self.w3af = w3af
        self.wizard = wizard
        super(QuestOptions,self).__init__()

        self.widg = gtk.Label("")
        self.pack_start(self.widg)
        self.activeQuestion = None
        
        self.show_all()

    def saveOptions(self):
        '''Saves the changed options.'''
        options = self.widg.options
        invalid = []
        
        for opt in options:
            #       Trying to reproduce bug 
            #       https://sourceforge.net/tracker2/?func=detail&aid=2652434&group_id=170274&atid=853652
            #
            #       To get more info:
            try:
                opt.widg
            except Exception, e:
                raise Exception(str(e) + ' || ' + opt.getName())
            # end of debugging code
                
            
            if hasattr(opt.widg, "isValid"):
                if not opt.widg.isValid():
                    invalid.append(opt.getName())
        if invalid:
            msg = "The configuration can't be saved, there is a problem in the following parameter(s):\n\n"
            msg += "\n-".join(invalid)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title('Configuration error')
            dlg.run()
            dlg.destroy()
            return

        for opt in options:
            opt.setValue( opt.widg.getValue() )

        try:
            helpers.coreWrap(self.wizard.setAnswer, options)
        except w3afException:
            return
        return True

    def configChanged(self, flag):
        # just to comply with API
        pass

    def setQuestOptions(self, quest):
        self.activeQuestion = quest
        self.remove(self.widg)
        self.widg = confpanel.OnlyOptions(self, self.w3af, Quest(quest), gtk.Button(), gtk.Button())
        self.pack_start(self.widg)

    def askFinal(self):
        # the text entries
        table = gtk.Table(2, 2)
        for row,tit in enumerate(("Name", "Description")):
            titlab = gtk.Label(tit)
            titlab.set_alignment(0.0, 0.5)
            table.attach(titlab, 0,1,row,row+1)
            entry = gtk.Entry()
            table.attach(entry, 1,2,row,row+1)
        table.show_all()
        # insert it
        self.remove(self.widg)
        self.widg = table
        self.pack_start(self.widg)

class Wizard(entries.RememberingWindow):
    '''The wizard to help the user to create a profile.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, wizard):
        super(Wizard,self).__init__(
            w3af, "wizard", "w3af Wizard: " + wizard.getName(), "Wizards",
            guessResize=False)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af
        self.wizard = wizard

        # the image at the left
        mainhbox = gtk.HBox()
        self.vbox.pack_start(mainhbox)
        leftframe = gtk.image_new_from_file('core/ui/gtkUi/data/wizard_frame.png')
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
        '''Saves all the info to a profile.'''
        filename = self.panel.widg.get_children()[2].get_text()
        description = self.panel.widg.get_children()[0].get_text()
        if not filename:
            msg = "The configuration can't be saved, you need to insert a profile name!\n\n"
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title('Missing info')
            dlg.run()
            dlg.destroy()
            return

        filename = cgi.escape(filename)
        try:
            helpers.coreWrap(self.w3af.profiles.saveCurrentToNewProfile, filename , description)
        except w3afException:
            self.w3af.mainwin.sb(_("There was a problem saving the profile!"))
            return
        self.w3af.mainwin.profiles.loadProfiles(filename)
        self.w3af.mainwin.sb(_("New profile created"))
        self.destroy()

    def _goNext(self, widg):
        '''Shows the next question.'''
        if self.finalQ:
            self._saveEverything()
            return
        if not self.panel.saveOptions():
            return
        quest = self.wizard.next()
        self.prevbtn.set_sensitive(True)
        if quest is None:
            self._buildFinal()
        else:
            self._buildWindow(quest)

    def _goBack(self, widg):
        '''Shows the previous question.'''
        if not self.finalQ:
            if not self.panel.saveOptions():
                return
        self.finalQ = False
        quest = self.wizard.previous()
        if quest is self._firstQuestion:
            self.prevbtn.set_sensitive(False)
        self._buildWindow(quest)

    def _buildWindow(self, question):
        '''Builds the useful pane for a question.

        @param question: the question with the info to build.
        '''
        self.qtitle.set_markup("<b>%s</b>" % question.getQuestionTitle())
        self.quest.set_text(question.getQuestionString())
        self.panel.setQuestOptions(question)
        self.nextbtn.set_label("  Next  ")
        self.finalQ = False

    def _buildFinal(self):
        '''End titles window.'''
        self.qtitle.set_markup("<b>The wizard has finished</b>")
        self.quest.set_text("There are no more questions, you correctly created a new "
                            "configuration for w3af.\n\nPlease provide a name and a "
                            "description for the new profile:")
        self.panel.askFinal()
        self.nextbtn.set_label("  Save  ")
        self.finalQ = True

class SimpleRadioButton(gtk.VBox):
    '''Simple to use radiobutton.'''
    def __init__(self, callback):
        super(SimpleRadioButton,self).__init__()
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
    '''Window that let's the user to choose a Wizard.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(WizardChooser,self).__init__(
            w3af, "wizardchooser", "w3af - Wizard Chooser", "Wizards", 
            guessResize=False)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af

        # the image at the left
        mainhbox = gtk.HBox()
        self.vbox.pack_start(mainhbox)
        leftframe = gtk.image_new_from_file('core/ui/gtkUi/data/wizard_frame.png')
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
        mainvbox.pack_start(l, False, False, padding = 10)

        # radiobutton and descrip
        innerbox = gtk.HBox()
        self.rbuts = SimpleRadioButton(self._changedRB)
        initlabel = None
        for wiz in self._getWizards():
            if initlabel is None:
                initlabel = wiz.getWizardDescription()
            self.rbuts.add(wiz.getName(), wiz)
        innerbox.pack_start(self.rbuts, True, False)

        self.wizdesc = gtk.Label(initlabel)
        innerbox.pack_start(self.wizdesc, padding=10)
        mainvbox.pack_start(innerbox, True, False)

        # go button
        buthbox = gtk.HBox()
        gobtn = gtk.Button("Run the wizard")
        gobtn.connect("clicked", self._goWizard)
        buthbox.pack_start(gobtn, True, False)
        mainvbox.pack_start(buthbox, False, False, padding = 10)
        
        # Show all!
        self.show_all()

    def _changedRB(self, widget):
        '''The radiobutton changed.'''
        self.wizdesc.set_label(widget.getWizardDescription())

    def _goWizard(self, widget):
        '''Runs the selected wizard.'''
        # First, clean all the enabled plugins that the user may have selected:
        for ptype in self.w3af.plugins.getPluginTypes():
            self.w3af.plugins.setPlugins([], ptype)
        
        # Destroy myself
        self.destroy()
        
        # Run the selected wizard
        Wizard(self.w3af, self.rbuts.active)

    def _getWizards(self):
        '''Returns the existing wizards.'''
        wizs = []
        for arch in os.listdir("core/controllers/wizard/wizards"):
            if arch.endswith(".py") and not arch.startswith("__"):
                base = arch[:-3]
                modbase = __import__("core.controllers.wizard.wizards."+base, fromlist=[None])
                cls = getattr(modbase, base)
                wizard_instance = cls( self.w3af )
                wizs.append(wizard_instance)
        return wizs
