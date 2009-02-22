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

import gtk, gobject
import threading
from . import history, helpers
import re


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

    def reset(self):
        '''Resets to the default value.'''
        self._setDefault(None, None)
        self._changed(None)
        
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
        text = self.get_text()
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
    def __init__(self, alert, opt):
        ValidatedEntry.__init__(self, opt.getValueStr())
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
    def __init__(self, alert, opt):
        ValidatedEntry.__init__(self, opt.getValueStr())
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
    def __init__(self, alert, opt):
        ValidatedEntry.__init__(self, opt.getValueStr())
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = ""

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return Always True, there's no validation to perform
        '''
        return True

class IPPortOption(ValidatedEntry, ModifiedMixIn):
    '''Class that implements the config option IP and Port.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, opt):
        ValidatedEntry.__init__(self, opt.getValueStr())
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = ""

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return True if valid.
        '''
        parts = text.split(":")
        return ( len(parts) == 2 and parts[1].isdigit() )

class ListOption(ValidatedEntry, ModifiedMixIn):
    '''Class that implements the config option List.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, opt):
        ValidatedEntry.__init__(self, opt.getValueStr())
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = ""

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return Always True, there's no validation to perform
        '''
        return True

class RegexOption(ValidatedEntry, ModifiedMixIn):
    '''Class that implements the config option regex.

    @author: Andres Riancho
    '''
    def __init__(self, alert, opt):
        ValidatedEntry.__init__(self, opt.getValueStr())
        ModifiedMixIn.__init__(self, alert, "changed", "get_text", "set_text")
        self.default_value = ""

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return: True if the regex compiles.
        '''
        try:
            re.compile(text)
        except:
            return False
        else:
            return True
        
class BooleanOption(gtk.CheckButton, ModifiedMixIn):
    '''Class that implements the config option Boolean.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, alert, opt):
        gtk.CheckButton.__init__(self)
        if opt.getValueStr() == "True":
            self.set_active(True)
        ModifiedMixIn.__init__(self, alert, "toggled", "get_active", "set_active")
        self.show()

class ComboBoxOption(gtk.ComboBox,  ModifiedMixIn):
    '''Class that implements the config option ComboBox.

    @author: Andres Riancho
    '''
    def __init__(self, alert, opt):
        self._opt = opt
        
        # Create the list store
        liststore = gtk.ListStore(str)
        optselected = opt.getValueStr()
        indselected = 0
        for i,option in enumerate(opt.getComboOptions()):
            if optselected == option:
                indselected = i
            liststore.append([option])
        
        gtk.ComboBox.__init__(self, liststore)
        
        # default option
        self.set_active(indselected)

        ModifiedMixIn.__init__(self, alert, "changed", "get_value", "set_value")

        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        
        self.show()
        
    def get_value(self):
        model = self.get_model()
        index = self.get_active()
        return model[index][0]
            
    def set_value(self,  t):
        index = self._opt.getValue().index(t)
        self.set_active(index)
        
    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return True if the text is ok.
        '''
        if text in self._opt.getComboOptions():
            return True
        else:
            return False

class SemiStockButton(gtk.Button):
    '''Takes the image from the stock, but the label which is passed.
    
    @param text: the text that will be used for the label
    @param image: the stock widget from where extract the image
    @param tooltip: the tooltip for the button

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, text, image, tooltip=None):
        super(SemiStockButton,self).__init__(stock=image)
        align = self.get_children()[0]
        box = align.get_children()[0]
        (self.image, self.label) = box.get_children()
        self.label.set_text(text)
        if tooltip is not None:
            self.set_tooltip_text(tooltip)
            
    def changeInternals(self, newtext, newimage, tooltip=None):
        '''Changes the image and label of the widget.
    
        @param newtext: the text that will be used for the label
        @param newimage: the stock widget from where extract the image
        @param tooltip: the tooltip for the button
        '''
        self.label.set_text(newtext)
        self.image.set_from_stock(newimage, gtk.ICON_SIZE_BUTTON)
        if tooltip is not None:
            self.set_tooltip_text(tooltip)


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

    def changeInternals(self, newlabel, newimage, newtooltip):
        '''Changes the image and label of the widget.
    
        @param newlabel: the text that will be used for the label
        @param newimage: the stock widget from where extract the image
        @param newtooltip: the text for the tooltip
        '''
        self.toolbut.set_tooltip_text(newtooltip)
        self.toolbut.set_label(newlabel)
        self.toolbut.set_property("stock-id", newimage)

    def set_sensitive(self, sensit):
        '''Sets the sensitivity of the toolbar button.'''
        self.toolbut.set_sensitive(sensit)

class AdvisedEntry(gtk.Entry):
    '''Entry that cleans its helping text the first time it's used.
    
    @param alertb: the function to call to activate when it was used
    @param message: the message to show in the entry at first and in
                    the tooltip

    The alertb calling is ready to work with the PropagationBuffer helper.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, message, alertb=None, historyfile=None, alertmodif=None):
        super(AdvisedEntry,self).__init__()
        self.connect("focus-in-event", self._focus)
        self.firstfocus = True
        self.origMessage = message
        self.set_text(message)
        self.alertb = alertb
        if self.alertb is not None:
            self.alertb(self, False)
        tooltips = gtk.Tooltips()
        tooltips.set_tip(self, message)

        if alertmodif is not None:
            self.alertmodif = alertmodif
            self.connect("changed", self._changed)

        # suggestion handling if history file is passed
        if historyfile is not None:
            self.hist = history.HistorySuggestion(historyfile)

            completion = gtk.EntryCompletion()
            self.liststore = gtk.ListStore(str)
            self.histtexts = self.hist.getTexts()
            for s in self.histtexts:
                self.liststore.append([s])

            completion.set_model(self.liststore)
            completion.set_match_func(self._match_completion)
            completion.set_text_column(0)
            self.set_completion(completion)
        else:
            self.hist = None

        self.show()

    def _changed(self, widg):
        self.alertmodif(changed = self.get_text() != self.origMessage)

    def _focus(self, *vals):
        '''Cleans it own text.'''
        if self.firstfocus:
            if self.alertb is not None:
                self.alertb(self, True)
            self.firstfocus = False
            self.set_text("")

    def _match_completion(self, completion, entrystr, iterl):
        '''Called when there's a match in the completion.'''
        texto = self.liststore[iterl][0]
        return entrystr in texto

    def setText(self, message):
        '''Sets the widget text.'''
        self.firstfocus = False
        self.origMessage = message
        self.set_text(message)
        
    def reset(self):
        '''Resets the message in the widget.'''
        self.firstfocus = True
        self.set_text(self.origMessage)
        
    def insertURL(self, *w):
        '''Saves the URL in the history infrastructure.'''
        if self.hist is not None:
            txt = self.get_text()
            if txt not in self.histtexts:
                self.liststore.insert(0, [txt])
            self.hist.insert(txt)
            self.hist.save()


class EntryDialog(gtk.Dialog):
    '''A dialog with a textentry.

    @param title: The title of the window

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title, stockok, options):
        super(EntryDialog,self).__init__(title, None, gtk.DIALOG_MODAL,
                      (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,stockok,gtk.RESPONSE_OK))

        # the text entries
        self.entries = []
        table = gtk.Table(len(options), 2)
        for row,tit in enumerate(options):
            titlab = gtk.Label(tit)
            titlab.set_alignment(0.0, 0.5)
            table.attach(titlab, 0,1,row,row+1)
            entry = gtk.Entry()
            entry.connect("changed", self._checkEntry)
            entry.connect("activate", self._setInputText, True)
            table.attach(entry, 1,2,row,row+1)
            self.entries.append(entry)
        self.vbox.pack_start(table)

        # the cancel button
        self.butt_cancel = self.action_area.get_children()[1]
        self.butt_cancel.connect("clicked", lambda x: self.destroy())

        # the saveas button
        self.butt_saveas = self.action_area.get_children()[0]
        self.butt_saveas.set_sensitive(False)
        self.butt_saveas.connect("clicked", self._setInputText)

        self.inputtexts = None
        self.show_all()

    def _setInputText(self, widget, close=False):
        '''Checks the entry to see if it has text.
        
        @param close: If True, the Dialog will be closed.
        '''
        if not self._allWithText():
            return
        self.inputtexts = [x.get_text() for x in self.entries]
        if close:
            self.response(gtk.RESPONSE_OK)

    def _allWithText(self):
        '''Checks if the entries has text.

        @return: True if all have text.
        '''
        for e in self.entries:
            if not e.get_text():
                return False
        return True

    def _checkEntry(self, *w):
        '''Checks the entry to see if it has text.'''
        self.butt_saveas.set_sensitive(self._allWithText())


class TextDialog(gtk.Dialog):
    '''A dialog with a textview, fillable from outside

    @param title: The title of the window

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title):
        super(TextDialog,self).__init__(title, None, gtk.DIALOG_MODAL,
                                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        # the textview inside scrollbars
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textview = gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(gtk.WRAP_WORD)
        self.textbuffer = self.textview.get_buffer()
        sw.add(self.textview)
        self.vbox.pack_start(sw)

        # the ok button
        self.butt_ok = self.action_area.get_children()[0]
        self.butt_ok.connect("clicked", self._handle_click )
        self.butt_ok.set_sensitive(False)
        
        self.wait = True

        self.resize(450,300)
        self.show_all()

    def run(self):
        raise Exception('Please use dialog_run().')

    def _handle_click(self, widg):
        '''
        Handle the Ok button click.
        '''
        self.wait = False

    def addMessage(self, text):
        '''Adds a message to the textview.

        @param text: the message to add.
        '''
        iterl = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iterl, text)
        self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0)
        
    def done(self):
        '''Actives the OK button, waits for user, and close self.'''
        self.butt_ok.set_sensitive(True)
    
    def dialog_response_cb(self, widget, response_id):
        '''
        http://faq.pygtk.org/index.py?req=show&file=faq10.017.htp
        '''
        self.destroy()

    def dialog_run(self):
        '''
        http://faq.pygtk.org/index.py?req=show&file=faq10.017.htp
        '''
        if not self.modal:
            self.set_modal(True)
        self.connect('response', self.dialog_response_cb)
        self.show()


class Searchable(object):
    '''Class that gives the machinery to search to a TextView.

    Just inheritate it from the box that has the textview to extend.

    @param textview: the textview to extend
    @param small: True if the buttons will only have the icons

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, textview, small=False):
        self.textview = textview
        self.small = small
        
        # By default, don't match case
        self._matchCaseValue = False
        
        # key definitions
        self.key_f = gtk.gdk.keyval_from_name("f")
        self.key_g = gtk.gdk.keyval_from_name("g")
        self.key_G = gtk.gdk.keyval_from_name("G")
        self.key_F3 = gtk.gdk.keyval_from_name("F3")

        # signals
        self.connect("key-press-event", self._key)
        self.textview.connect("populate-popup", self._populate_popup)

        # colors for textview and entry backgrounds
        self.textbuf = self.textview.get_buffer()
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
                self.show_search()
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
        opc = gtk.MenuItem(_("Find..."))
        menu.append(opc)
        opc.connect("activate", self.show_search)
        menu.show_all()

    def show_search(self, widget=None):
        '''Shows the search tab.'''
        self.srchtab.show_all()
        self.search_entry.grab_focus()
        self.searching = True

    def _build_search(self, widget):
        '''Builds the search bar.'''
        tooltips = gtk.Tooltips()
        self.srchtab = gtk.HBox()
        
        # close button
        close = gtk.Image()
        close.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        eventbox = gtk.EventBox()
        eventbox.add(close)
        eventbox.connect("button-release-event", self._close)
        self.srchtab.pack_start(eventbox, expand=False, fill=False, padding=3)

        # label
        label = gtk.Label("Find:")
        self.srchtab.pack_start(label, expand=False, fill=False, padding=3)

        # entry
        self.search_entry = gtk.Entry()
        tooltips.set_tip(self.search_entry, _("Type here the phrase you want to find"))
        self.search_entry.connect("activate", self._find, "next")
        self.search_entry.connect("changed", self._find, "find")
        self.srchtab.pack_start(self.search_entry, expand=False, fill=False, padding=3)

        # find next button
        if self.small:
            but_text = ''
        else:
            but_text = 'Next'
        butn = SemiStockButton(but_text, gtk.STOCK_GO_DOWN)
        butn.connect("clicked", self._find, "next")
        tooltips.set_tip(butn, _("Find the next ocurrence of the phrase"))
        self.srchtab.pack_start(butn, expand=False, fill=False, padding=3)

        # find previous button
        if self.small:
            but_text = ''
        else:
            but_text = ('Previous')
        butp = SemiStockButton(but_text, gtk.STOCK_GO_UP)
        butp.connect("clicked", self._find, "previous")
        tooltips.set_tip(butp, _("Find the previous ocurrence of the phrase"))
        self.srchtab.pack_start(butp, expand=False, fill=False, padding=3)

        # make last two buttons equally width
        wn,hn = butn.size_request()
        wp,hp = butp.size_request()
        newwidth = max(wn, wp)
        butn.set_size_request(newwidth, hn)
        butp.set_size_request(newwidth, hp)
        
        # Match case CheckButton
        butCase = gtk.CheckButton(_('Match case'))
        butCase.set_active(self._matchCaseValue)
        butCase.connect("clicked", self._matchCase)
        butCase.show()
        self.srchtab.pack_start(butCase, expand=False, fill=False, padding=3)

        self.pack_start(self.srchtab, expand=False, fill=False)
        self.searching = False

    def _matchCase(self, widg):
        '''
        Toggles self._matchCaseValue and searches again
        '''
        self._matchCaseValue = not self._matchCaseValue
        self._find(None, 'find')
        

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

        if not self._matchCaseValue:
            alltext = alltext.lower()
            tosearch = tosearch.lower()

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
        self.textview.scroll_to_iter(iterini, 0, False)

    def _close(self, widget, event):
        '''Hides the search bar, and cleans the background.'''
        self.srchtab.hide()
        self._clean()
        self.searching = False

    def _clean(self):
        '''Cleans the entry colors.'''
        # highlights
        (ini, fin) = self.textbuf.get_bounds()
        self.textbuf.remove_tag_by_name("yellow-background", ini, fin)

        # entry background
        self.search_entry.modify_base(gtk.STATE_NORMAL, self.bg_normal)



class RememberingWindow(gtk.Window):
    '''Just a window that remembers position and size.

    Also has a vertical box for the content.

    @param w3af: the w3af core
    @param idstring: an id for the configuration
    @param title: the window title
    @param helpid: the chapter of the help guide
    @param onDestroy: a function (if not None) that will be called when the 
                      user wants to close the window. If returns False the
                      window is not closed.
    @param guessResize: if there's no saved configuration for the window, 
                        the system will guess the size or not.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, idstring, title, helpid='', onDestroy=None, guessResize=True):
        super(RememberingWindow,self).__init__(gtk.WINDOW_TOPLEVEL)
        self.onDestroy = onDestroy
        self.helpid = helpid

        # position and dimensions
        self.winconfig = w3af.mainwin.generalconfig
        self.id_size = idstring + "-size"
        self.id_position = idstring + "-position"
        conf_position = self.winconfig.get(self.id_position, (100, 100))
        self.move(*conf_position)
        if guessResize or self.id_size in self.winconfig:
            conf_size = self.winconfig.get(self.id_size, (1000, 500))
            self.resize(*conf_size)

        # main vertical box
        self.vbox = gtk.VBox()
        self.vbox.show()
        self.add(self.vbox)

        self.set_title(title)
        self.connect("delete_event", self.quit)
        self.connect('key_press_event', self.helpF1)

    def helpF1(self, widget, event):
        if event.keyval != 65470: # F1, check: gtk.gdk.keyval_name(event.keyval)
            return

        helpers.open_help(self.helpid)


    def quit(self, widget, event):
        '''Windows quit, saves the position and size.

        @param widget: who sent the signal.
        @param event: the event that happened
        '''
        if self.onDestroy is not None:
            if not self.onDestroy():
                return True

        self.winconfig[self.id_size] = self.get_size()
        self.winconfig[self.id_position] = self.get_position()
        return False


class PagesEntry(ValidatedEntry):
    '''The entry for the PagesControl.

    @param maxval: the maxvalue it can hold

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    
    def __init__(self, maxval):
        self.maxval = maxval
        self.default_value = "1"
        ValidatedEntry.__init__(self, "1")

    def setMax(self, maxval):
        '''Sets the max value for the entry.'''
        self.maxval = maxval
        self.reset()

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return Always True, there's no validation to perform
        '''
        try:
            num = int(text)
        except ValueError:
            return False
        # the next check is because it's shown +1
        return (0 < num <= self.maxval)

class PagesControl(gtk.HBox):
    '''The control to pass the pages.

    @param w3af: the w3af core
    @param callback: the function to call back when a page is changed.
    @param maxpages: the quantity of pages.

    maxpages is optional, but the control will be greyed out until the 
    max is passed in the activate() method.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, callback, maxpages=None):
        self.w3af = w3af
        gtk.HBox.__init__(self)
        self.callback = callback
        self.page = 1

        self.left = gtk.Button()
        self.left.connect("clicked", self._arrow, -1)
        self.left.add(gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_OUT))

        self.pack_start(self.left, False, False)
        self.pageentry = PagesEntry(maxpages)
        self.pageentry.connect("activate", self._textpage)
        self.pageentry.set_width_chars(5)
        self.pageentry.set_alignment(.5)
        self.pack_start(self.pageentry, False, False)

        self.total = gtk.Label()
        self.pack_start(self.total, False, False)

        self.right = gtk.Button()
        self.right.connect("clicked", self._arrow, 1)
        self.right.add(gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_OUT))
        self.pack_start(self.right, False, False)

        if maxpages is None:
            self.set_sensitive(False)
        else:
            self.total.set_text(" of %d " % maxpages)
            self.maxpages = maxpages
            self._arrow()
        self.show_all()

    def deactivate(self):
        self.set_sensitive(False)
        self.right.set_sensitive(False)
        self.left.set_sensitive(False)
        self.total.set_text("")
        self.pageentry.set_text("0")
        
    def activate(self, maxpages):
        self.maxpages = maxpages
        self.total.set_text(" of %d " % maxpages)
        self.pageentry.setMax(maxpages)
        self.set_sensitive(True)
        self._arrow()

    def _textpage(self, widg):
        val = self.pageentry.get_text()
        if not self.pageentry.isValid():
            self.w3af.mainwin.sb(_("%r is not a good value!") % val)
            return
        self.setPage(int(val))
        
    def setPage(self, page):
        self.page = page
        self._arrow()
            
    def _arrow(self, widg=None, delta=0):
        self.page += delta

        # limit control, with a +1 shift
        if self.page < 1:
            self.page = 1
        elif self.page > self.maxpages:
            self.page = self.maxpages

        # entries adjustment
        self.left.set_sensitive(self.page > 1)
        self.right.set_sensitive(self.page < self.maxpages)
        self.pageentry.set_text(str(self.page))
        self.callback(int(self.page)-1)


class EasyTable(gtk.Table):
    '''Simplification of gtk.Table.

    @param arg: all it receives goes to gtk.Table
    @param kw: all it receives goes to gtk.Table

    This class is to have a simple way to add rows to the table.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, *arg, **kw):
        super(EasyTable,self).__init__(*arg, **kw)
        self.auto_rowcounter = 0
        self.set_row_spacings(1)

    def autoAddRow(self, *widgets):
        '''Simple way to add rows to a table.

        @param widgets: all the widgets to the row

        This method creates a new row, adds the widgets and show() them.
        '''
        r = self.auto_rowcounter
        for i,widg in enumerate(widgets):
            if widg is not None:
                self.attach(widg, i, i+1, r, r+1, yoptions=gtk.EXPAND, xpadding=5)
                widg.show()
        self.auto_rowcounter += 1

# decision of which widget implements the option to each type
wrapperWidgets = {
    "boolean": BooleanOption,
    "integer": IntegerOption,
    "string": StringOption,
    "ipport": IPPortOption,
    "float": FloatOption,
    "list": ListOption,
    "combo": ComboBoxOption, 
    "regex": RegexOption, 
}


# three classes to provide remembering panes

class _RememberingPane(object):
    '''Remembering pane class.

    Don't use it directly, you should use the ones provided below this.

    @param w3af: the core
    @param widgname: the name of the widget (the remembering key)
    @param dimension: 0 for hztal, 1 for vertical
    @param defaultInitPos: the default position for the first time 
                           (overrides "half of the screen").
    '''
    def __init__(self, w3af, widgname, dimension, defaultInitPos=None):
        self.connect("notify", self.moveHandle)
        self.winconfig = w3af.mainwin.generalconfig
        self.widgname = widgname
        self.dimension = dimension

        # if we have it from before, get the info; otherwise plan to
        # set it up around its half
        if widgname in self.winconfig:
            self.set_position(self.winconfig[widgname])
        elif defaultInitPos is not None:
            self.set_position(defaultInitPos)
            self.winconfig[self.widgname] = defaultInitPos
        else:
            self.signal = self.connect("expose-event", self.exposed)
        
    def moveHandle(self, widg, what):
        '''Adjust the record every time the handle is moved.'''
        if what.name == "position-set":
            pos = self.get_position()
            self.winconfig[self.widgname] = pos

    def exposed(self, area, event):
        '''Adjust the handle to the remembered position.

        This is done only once.
        '''
        altoancho = self.window.get_size()[self.dimension]
        newpos = altoancho//2
        self.set_position(newpos)
        self.winconfig[self.widgname] = newpos
        self.disconnect(self.signal)
        return True

class RememberingHPaned(gtk.HPaned, _RememberingPane):
    '''Remembering horizontal pane.

    @param w3af: the core
    @param widgname: the name of the widget (the remembering key)
    @param defPos: the default position for the first time (overrides 
                   "half of the screen").
    '''
    def __init__(self, w3af, widgname, defPos=None):
        gtk.HPaned.__init__(self)
        _RememberingPane.__init__(self, w3af, widgname, 0, defPos)

class RememberingVPaned(gtk.VPaned, _RememberingPane):
    '''Remembering vertical pane.

    @param w3af: the core
    @param widgname: the name of the widget (the remembering key)
    @param defPos: the default position for the first time (overrides 
                   "half of the screen").
    '''
    def __init__(self, w3af, widgname, defPos=None):
        gtk.VPaned.__init__(self)
        _RememberingPane.__init__(self, w3af, widgname, 1, defPos)


class StatusBar(gtk.Statusbar):
    '''All status bar functionality.
    
    @param initmsg: An optional initial message.
    @param others : Others widgets to add at the right of the texts.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, initmsg=None, others=[]):
        super(StatusBar,self).__init__()
        self._context = self.get_context_id("unique_sb")
        self._timer = None

        # add the others
        for oth in others[::-1]:
            self.pack_end(oth, False)
            self.pack_end(gtk.VSeparator(), False)

        if initmsg is not None:
            self.__call__(initmsg)

        self.show_all()
        
    def __call__(self, msg, timeout=5):
        '''Inserts a message in the statusbar.'''
        if self._timer is not None:
            self._timer.cancel()
        self.push(self._context, msg)
        self._timer = threading.Timer(timeout, self.clear, ())
        self._timer.start()

    def clear(self):
        '''Clears the statusbar content.'''
        self.push(self._context, "")
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
