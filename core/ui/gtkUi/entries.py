'''
entries.py

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

import pygtk
pygtk.require('2.0')
import gtk

class ValidatedEntry(gtk.Entry):
    '''Class to perform some validations in gtk.Entry.
    
    @param value: The initial value of the widget

    For each keystroke, it validates the input and tell you if you're
    ok with a good background, or bad with a warning one.
    
    If the user left the widget in some blank state, a value "empty"
    default will be used.
    
    If the user presses Esc, it will undo the changes.
    
    The one who subclass this needs to define:

        - validate(): method that returns True if the text is ok
        - default_value: how to fill the entry when user leaves it empty

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, value):
        super(ValidatedEntry,self).__init__()
        self.connect("changed", self._changed)
        self.connect("focus-out-event", self._setDefault)
        self.connect("key-release-event", self._key)
        self.orig_value = value
        self.esc_key = gtk.gdk.keyval_from_name("Escape") 

        # color handling
        colormap = self.get_colormap()
        self.bg_normal = colormap.alloc_color("white")
        self.bg_badentry = colormap.alloc_color("yellow")

        self.set_text(value)
        self.show()

    def _key(self, widg, event):
        '''Signal handler for 'key-release-event' event.

        @param widg: widget who signaled
        @param event: event happened

        Used to supervise if user presses Esc, to restore original
        widget value.
        '''
        if event.keyval == self.esc_key:
            self.set_text(self.orig_value)
        
    def _setDefault(self, widg, event):
        '''Signal handler for 'focus-out-event' event.

        @param widg: widget who signaled
        @param event: event happened

        Used to put the default value if the user left the
        widget leaving it empty.
        '''
        if self.get_text() == "":
            self.set_text(self.default_value)

    def _changed(self, widg):
        '''Signal handler for 'changed' event.

        @param widg: widget who signaled

        Used to supervise if the widget value is ok or not.
        '''
        text = widg.get_text()
        # background color indicates validity
        if self.validate(text):
            self.modify_base(gtk.STATE_NORMAL, self.bg_normal)
        else:
            self.modify_base(gtk.STATE_NORMAL, self.bg_badentry)

    def validate(self, text):
        '''Validates the widget value.

        @param text: the text of the widget
        @raises NotImplementedError: if the method is not redefined
        
        It will called everytime the widget value changes. 

        The redefined method must return True if the text is valid.
        '''
        raise NotImplementedError

    def isValid(self):
        '''Checks if the widget value is valid.

        @return: True if the widget is in a valid state.
        '''
        return self.validate(self.get_text())

class ModifiedMixIn(object):
    '''Mix In class for modified/initial status.

    This class adds the functionality of alerting to something each
    time the widget is modified, telling it if the widget has the initial
    value or not. It also provides a revertValue method to revert the
    value of the widget to its initial state.

    @param alert: the function it will call to alert about a change
    @param signal: the signal that is issued every time the widget changes
    @param getvalue: the method of the widget to retrieve its value
    @param setvalue: the method of the widget to set its value

    Note that the initial value is stored calling this last very function. 
    So, this mixin class needs to be initialized after setting the value
    of the widget (this is also necessary to not raise the alert in 
    this initial setup).

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''

    def __init__(self, alert, signal, getvalue, setvalue):
        self.getfunct = getattr(self, getvalue)
        self.setfunct = getattr(self, setvalue)
        self.initvalue = self.getfunct()
        self.alert = alert
        self.connect(signal, self._checkInitial)
        
    def _checkInitial(self, widg):
        '''Signal handler for the configured signal.

        Checks if the actual value is the initial one.

        @param widg: widget who signaled

        In any case generates the alert to propagate the state.
        '''
        self.alert(self, self.getfunct() == self.initvalue)

    def revertValue(self):
        '''Returns the widget to its last saved state.'''
        self.setfunct(self.initvalue)

    def getValue(self):
        '''Queries the value of the widget.
        
        @return: The value of the widget.
        '''
        val = self.getfunct()
        return str(val)

    def save(self):
        '''Store current value as the initial one. '''
        self.initvalue = self.getfunct()
        self.alert(self, True)


class IntegerOption(ValidatedEntry, ModifiedMixIn):
    '''Class that implements the config option Integer.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, value):
        ValidatedEntry.__init__(self, value)
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = "0"

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return True if the text is ok.

        Validates if int() is ok with the received text.
        '''
        try:
            int(text)
        except:
            return False
        return True

class FloatOption(ValidatedEntry, ModifiedMixIn):
    '''Class that implements the config option Float.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, value):
        ValidatedEntry.__init__(self, value)
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = "0.0"

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return True if the text is ok.

        Validates if float() is ok with the received text.
        '''
        try:
            float(text)
        except:
            return False
        return True

class StringOption(ValidatedEntry, ModifiedMixIn):
    '''Class that implements the config option String.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, value):
        ValidatedEntry.__init__(self, value)
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = ""

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return Always True, there's no validation to perform
        '''
        return True

class ListOption(ValidatedEntry, ModifiedMixIn):
    '''Class that implements the config option List.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, value):
        ValidatedEntry.__init__(self, value)
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = ""

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return Always True, there's no validation to perform
        '''
        return True

class BooleanOption(gtk.CheckButton, ModifiedMixIn):
    '''Class that implements the config option Boolean.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, value):
        gtk.CheckButton.__init__(self)
        if value == "True":
            self.set_active(True)
        ModifiedMixIn.__init__(self, alert, "toggled", "get_active", "set_active")
        self.show()


class SemiStockButton(gtk.Button):
    '''Takes the image from the stock, but the label which is passed.
    
    @param text: the text that will be used for the label
    @param image: the stock widget from where extract the image

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, text, image):
        super(SemiStockButton,self).__init__(stock=image)
        align = self.get_children()[0]
        box = align.get_children()[0]
        (self.image, self.label) = box.get_children()
        self.label.set_text(text)

    def changeInternals(self, newtext, newimage):
        '''Changes the image and label of the widget.
    
        @param newtext: the text that will be used for the label
        @param newimage: the stock widget from where extract the image
        '''
        self.label.set_text(newtext)
        self.image.set_from_stock(newimage, gtk.ICON_SIZE_BUTTON)


class AdvisedEntry(gtk.Entry):
    '''Entry that cleans its helping text the first time it's used.
    
    @param alertb: the button to activate when it was used
    @param message: the message to show in the entry at first and in
                    the tooltip

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, message, alertb=None):
        super(AdvisedEntry,self).__init__()
        self.connect("focus-in-event", self._focus)
        self.firstfocus = True
        self.set_text(message)
        self.alertb = alertb
        if self.alertb is not None:
            self.alertb.change(self, False)
        tooltips = gtk.Tooltips()
        tooltips.set_tip(self, message)
        self.show()

    def _focus(self, *vals):
        '''Cleans it own text.'''
        if self.firstfocus:
            if self.alertb is not None:
                self.alertb.change(self, True)
            self.firstfocus = False
            self.set_text("")


class TextDialog(gtk.Dialog):
    '''A dialog with a textview, fillable from outside

    @param title: The title of thw window

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title):
        super(TextDialog,self).__init__(title, None, gtk.DIALOG_MODAL,
                                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        # the textview
        textview = gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_wrap_mode(gtk.WRAP_WORD)
        self.textbuffer = textview.get_buffer()
        self.vbox.pack_start(textview)
        textview.show()

        # the ok button
        self.butt_ok = self.action_area.get_children()[0]
        self.butt_ok.connect("clicked", lambda x: self.destroy())
        self.butt_ok.set_sensitive(False)

        self.resize(300,200)
        self.show()
        self.flush()

    def flush(self):
        '''Flushes the GUI operations.'''
        while gtk.events_pending(): 
            gtk.main_iteration()

    def addMessage(self, text):
        '''Adds a message to the textview.

        @param text: the message to add.
        '''
        iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iter, text+"\n")
        self.flush()
        
    def done(self):
        '''Actives the OK button, waits for user, and close self.'''
        self.butt_ok.set_sensitive(True)
        self.run()
