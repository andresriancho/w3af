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


class ToolbuttonWrapper(object):
    '''Wraps a tool button from a toolbar, and offer helpers.
    
    @param toolbar: the toolbar to extract the toolbutton
    @param position: the position where it is

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, toolbar, position):
        self.toolbut = toolbar.get_nth_item(position)
        if self.toolbut is None:    
            raise ValueError("The toolbar does not have a button in position %d" % position)

        but = self.toolbut.get_children()[0]
        box = but.get_children()[0]
        self.image = box.get_children()[0]

    def changeInternals(self, newlabel, newimage, newtooltip):
        '''Changes the image and label of the widget.
    
        @param newlabel: the text that will be used for the label
        @param newimage: the stock widget from where extract the image
        @param newtooltip: the text for the tooltip
        '''
        self.toolbut.set_tooltip_text(newtooltip)
        self.toolbut.set_label(newlabel)
        box = self.toolbut.get_children()[0].get_children()[0]
        img = box.get_children()[0]
        img.set_from_stock(newimage, gtk.ICON_SIZE_BUTTON)

    def set_sensitive(self, sensit):
        self.toolbut.set_sensitive(sensit)

class AdvisedEntry(gtk.Entry):
    '''Entry that cleans its helping text the first time it's used.
    
    @param alertb: the function to call to activate when it was used
    @param message: the message to show in the entry at first and in
                    the tooltip

    The alertb calling is ready to work with the PropagationBuffer helper.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, message, alertb=None):
        super(AdvisedEntry,self).__init__()
        self.connect("focus-in-event", self._focus)
        self.firstfocus = True
        self.set_text(message)
        self.alertb = alertb
        if self.alertb is not None:
            self.alertb(self, False)
        tooltips = gtk.Tooltips()
        tooltips.set_tip(self, message)
        self.show()

    def _focus(self, *vals):
        '''Cleans it own text.'''
        if self.firstfocus:
            if self.alertb is not None:
                self.alertb(self, True)
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


class Searchable(object):
    '''Class that gives the machinery to search to a TextView.

    Just inheritate it.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        # key definitions
        self.key_f = gtk.gdk.keyval_from_name("f")
        self.key_g = gtk.gdk.keyval_from_name("g")
        self.key_G = gtk.gdk.keyval_from_name("G")
        self.key_F3 = gtk.gdk.keyval_from_name("F3")

        # signals
        self.connect("key-press-event", self._key)
        self.sclines.connect("populate-popup", self._populate_popup)

        # colors for textview and entry backgrounds
        self.textbuf = self.sclines.get_buffer()
        self.textbuf.create_tag("yellow-background", background="yellow")
        colormap = self.get_colormap()
        self.bg_normal = colormap.alloc_color("white")
        self.bg_notfnd = colormap.alloc_color("red")

        # build the search tab
        self._build_search(None)

    def _key(self, widg, event):
        '''Handles keystrokes.'''
        # ctrl-something
        if event.state & gtk.gdk.CONTROL_MASK:
            if event.keyval == self.key_f:   # -f
                self._show_search()
            elif event.keyval == self.key_g:   # -g
                self._find(None, "next")
            elif event.keyval == self.key_G:   # -G (with shift)
                self._find(None, "previous")
            return True

        # F3
        if event.keyval == self.key_F3:
            if event.state & gtk.gdk.SHIFT_MASK:
                self._find(None, "previous")
            else:
                self._find(None, "next")
        return False

    def _populate_popup(self, textview, menu):
        '''Populates the menu with the Find item.'''
        menu.append(gtk.SeparatorMenuItem())
        opc = gtk.MenuItem("Find...")
        menu.append(opc)
        opc.connect("activate", self._show_search)
        menu.show_all()

    def _show_search(self, widget=None):
        self.srchtab.show_all()
        self.search_entry.grab_focus()
        self.searching = True

    def _build_search(self, widget):
        '''Builds the search bar.'''
        tooltips = gtk.Tooltips()
        self.srchtab = gtk.HBox()

        # label
        label = gtk.Label("Find:")
        self.srchtab.pack_start(label, expand=False, fill=False, padding=3)

        # entry
        self.search_entry = gtk.Entry()
        tooltips.set_tip(self.search_entry, "Type here the phrase you want to find")
        self.search_entry.connect("activate", self._find, "next")
        self.search_entry.connect("changed", self._find, "find")
        self.srchtab.pack_start(self.search_entry, expand=False, fill=False, padding=3)

        # find next button
        butn = SemiStockButton("Next", gtk.STOCK_GO_DOWN)
        butn.connect("clicked", self._find, "next")
        tooltips.set_tip(butn, "Find the next ocurrence of the phrase")
        self.srchtab.pack_start(butn, expand=False, fill=False, padding=3)

        # find previous button
        butp = SemiStockButton("Previous", gtk.STOCK_GO_UP)
        butp.connect("clicked", self._find, "previous")
        tooltips.set_tip(butp, "Find the previous ocurrence of the phrase")
        self.srchtab.pack_start(butp, expand=False, fill=False, padding=3)

        # make last two buttons equally width
        wn,hn = butn.size_request()
        wp,hp = butp.size_request()
        newwidth = max(wn, wp)
        butn.set_size_request(newwidth, hn)
        butp.set_size_request(newwidth, hp)

        # close button
        close = gtk.Image()
        close.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_SMALL_TOOLBAR)
        eventbox = gtk.EventBox()
        eventbox.add(close)
        eventbox.connect("button-release-event", self._close)
        self.srchtab.pack_end(eventbox, expand=False, fill=False, padding=3)

        self.pack_start(self.srchtab, expand=False, fill=False)
        self.searching = False

    def _find(self, widget, direction):
        '''Actually find the text, and handle highlight and selection.'''
        # if not searching, don't do anything
        if not self.searching:
            return

        # get widgets and info
        self._clean()
        tosearch = self.search_entry.get_text()
        if not tosearch:
            return
        (ini, fin) = self.textbuf.get_bounds()
        alltext = self.textbuf.get_text(ini, fin)

        # find the positions where the phrase is found
        positions = []
        pos = 0
        while True:
            try:
                pos = alltext.index(tosearch, pos)
            except ValueError:
                break
            fin = pos + len(tosearch)
            iterini = self.textbuf.get_iter_at_offset(pos)
            iterfin = self.textbuf.get_iter_at_offset(fin)
            positions.append((pos, fin, iterini, iterfin))
            pos += 1
        if not positions:
            self.search_entry.modify_base(gtk.STATE_NORMAL, self.bg_notfnd)
            self.textbuf.select_range(ini, ini)
            return

        # highlight them all
        for (ini, fin, iterini, iterfin) in positions:
            self.textbuf.apply_tag_by_name("yellow-background", iterini, iterfin)

        # find where's the cursor in the found items
        cursorpos = self.textbuf.get_property("cursor-position")
        for ind, (ini, fin, iterini, iterfin) in enumerate(positions):
            if ini >= cursorpos:
                keypos = ind
                break
        else:
            keypos = 0

        # go next or previos, and adjust in the border
        if direction == "next":
            keypos += 1
            if keypos >= len(positions):
                keypos = 0
        elif direction == "previous":
            keypos -= 1
            if keypos < 0:
                keypos = len(positions) - 1
        
        # mark and show it
        (ini, fin, iterini, iterfin) = positions[keypos]
        self.textbuf.select_range(iterini, iterfin)
        self.sclines.scroll_to_iter(iterini, 0, False)

    def _close(self, widget, event):
        '''Hides the search bar, and cleans the background.'''
        self.srchtab.hide()
        self._clean()
        self.searching = False

    def _clean(self):
        # highlights
        (ini, fin) = self.textbuf.get_bounds()
        self.textbuf.remove_tag_by_name("yellow-background", ini, fin)

        # entry background
        self.search_entry.modify_base(gtk.STATE_NORMAL, self.bg_normal)


