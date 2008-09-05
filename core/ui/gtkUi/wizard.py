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

import gtk, os
from . import entries

#
#  FIXME!! Remove this old "API documentation"
#
# from core.controllers.w3afException import w3afException
# from core.controllers.wizard.wizards.short_wizard import short_wizard
# 
# 
# # View the questions in this step, and answer with null
# options = q1.getOptionObjects()
# for i in options:
#     print i.getDesc()
#     i.setValue('')
# 
# # this has to fail, because the question requires that
# # you enter some value in the field
# try:
#     sw.setAnswer(options)
# except Exception, e:
#     print 'Failed (as expected):', e
# 
# # Now we fill it with a valid value
# i.setValue('http://localhost/value_!')
# try:
#     sw.setAnswer(options)
# except Exception, e:
#     print 'Failed! (not expected... something went wrong):', e
# else:
#     print 'Ok'
# 
# # Now that we have setted the answer, we get the next question
# q2 = sw.next()
# print 'q2 title:', q1.getQuestionTitle()
# print 'q2 question:', q1.getQuestionString()
# 
# # The user doesn't change anything
# options = q2.getOptionObjects()
# sw.setAnswer(options)
# 
# if sw.next() == None:
#     print 'Finished the wizard'
# 
# # But wait! Now I remembered that I want to change something from the first question!
# sw.previous()
# q1 = sw.previous()
# print 'q1 title:', q1.getQuestionTitle()
# print 'q1 question:', q1.getQuestionString()
# print 'did we saved the value??'
# options = q1.getOptionObjects()
# for i in options:
#     print i.getValue()
# 

class Questions(gtk.VBox):
    def __init__(self):
        super(Questions,self).__init__()

        self.l = gtk.Label("puto")
        self.pack_start(self.l)
        
        self.show_all()

    def setQuestions(self, quest):
        self.l.set_text(str(id(quest)))

class Wizard(entries.RememberingWindow):
    '''The wizard to help the user to create a profile.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, wizard):
        super(Wizard,self).__init__(w3af, "wizard", "w3af Wizard: " + wizard.getName())
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af

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
        mainvbox.pack_start(self.quest, False, False, padding=10)
        self.panel = Questions()
        mainvbox.pack_start(self.panel, False, False, padding=10)

        # fill it
        quest = wizard.next()
        self._buildWindow(quest)

        # go button
        butbox = gtk.HBox()
        prevbtn = gtk.Button("  Back  ")
        prevbtn.connect("clicked", self._goBack)
        butbox.pack_start(prevbtn, True, False)
        nextbtn = gtk.Button("  Next  ")
        nextbtn.connect("clicked", self._goNext)
        butbox.pack_start(nextbtn, True, False)
        mainvbox.pack_start(butbox, False, False, padding = 10)
        
        # Show all!
        self.show_all()

    def _goNext(self, widg):
        print "Next!"
    def _goBack(self, widg):
        print "Back!"

    def _buildWindow(self, question):
        self.qtitle.set_markup("<b>%s</b>" % question.getQuestionTitle())
        self.quest.set_text(question.getQuestionString())
        self.panel.setQuestions(question)


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
        super(WizardChooser,self).__init__(w3af, "wizardchooser", "w3af - Wizard Chooser")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af

        # the image at the left
        mainhbox = gtk.HBox()
        self.vbox.pack_start(mainhbox)
        leftframe = gtk.image_new_from_file('core/ui/gtkUi/data/wizard_frame.png')
        mainhbox.pack_start(leftframe, False, False)
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
        innerbox.pack_start(self.wizdesc)
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
        self.destroy()
        Wizard(self.w3af, self.rbuts.active)

    def _getWizards(self):
        '''Returns the existing wizards.'''
        wizs = []
        for arch in os.listdir("core/controllers/wizard/wizards"):
            if arch.endswith(".py") and not arch.startswith("__"):
                base = arch[:-3]
                modbase = __import__("core.controllers.wizard.wizards."+base, fromlist=[None])
                cls = getattr(modbase, base)
                wizs.append(cls())
        return wizs
