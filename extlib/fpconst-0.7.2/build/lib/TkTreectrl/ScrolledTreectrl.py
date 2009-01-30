# -*- coding: iso-8859-1 -*-
'''Treectrl and MultiListbox widgets with scrollbars.'''

import Tkinter
import Treectrl
import MultiListbox

class ScrolledWidget(Tkinter.Frame):
    '''Base class for Tkinter widgets with scrollbars.
    The widget is a standard Tkinter.Frame with an additional configuration option
    SCROLLMODE which may be one of "x", "y", "both" or "auto".
    If SCROLLMODE is one of "x", "y" or "both", one or two static scrollbars will be
    drawn. If SCROLLMODE is set to "auto", two automatic scrollbars that appear only
    if needed will be drawn.
    The Scrollbar widgets can be accessed with the hbar and vbar class attributes.
    Derived classes must override the _setScrolledWidget() method, which must return
    the widget that will be scrolled and should add a class attribute that allows
    to access this widget, so the _setScrolledWidget() method for a ScrolledListbox
    widget might look like:
    
        def _setScrolledWidget(self):
            self.listbox = Tkinter.Listbox(self)
            return self.listbox
    
    Note that although it should be possible to create scrolled widget classes for
    virtually any Listbox or Canvas alike Tkinter widget you can *not* safely use
    this class to add automatic scrollbars to a Text or Text alike widget.
    This is because in a scrolled Text widget the value of the horizontal scrollbar
    depends only on the visible part of the Text, not on it's whole contents.
    Thus it may happen that it is the last visible line of text that causes the
    automatic scrollbar to be mapped which then hides this last line so it will be
    unmapped again, but then it is requested again and gets mapped and so on forever.
    There are strategies to avoid this, but usually at the cost that there will be
    situations where the horizontal scrollbar remains mapped although it is actually
    not needed. In order to acomplish this with the ScrolledWidget class, at least
    the _scrollXNow() and _scrollBothNow() methods must be overridden with appropriate
    handlers.
    '''
    def __init__(self, master=None, scrollmode='auto', **kw):
        if not kw.has_key('width'):
            kw['width'] = 400
        if not kw.has_key('height'):
            kw['height'] = 300
        Tkinter.Frame.__init__(self, master, **kw)
        # call grid_propagate(0) so the widget will not change its size
        # when the scrollbars are mapped or unmapped; that is why we need
        # to specify width and height in any case
        self.grid_propagate(0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self._scrollmode = scrollmode
        
        self._scrolledWidget = self._setScrolledWidget()
        self._scrolledWidget.grid(row=0, column=0, sticky='news')
        
        self.vbar = Tkinter.Scrollbar(self, orient='vertical', command=self._scrolledWidget.yview)
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.hbar = Tkinter.Scrollbar(self, orient='horizontal', command=self._scrolledWidget.xview)
        self.hbar.grid(row=1, column=0, sticky='ew')
        
        # Initialise instance variables.
        self._hbarOn = 1
        self._vbarOn = 1
        self._scrollTimer = None
        self._scrollRecurse = 0
        self._hbarNeeded = 0
        self._vbarNeeded = 0
        
        self._scrollMode(scrollmode)
    
    def _setScrolledWidget(self):
        '''This method must be overridden in derived classes.
        It must return the widget that should be scrolled and should
        add a reference to the ScrolledWidget object, so it can be accessed
        by the user. For example, to create a scrolled Listbox, do:
        self.listbox = Tkinter.Listbox(self)
        return self.listbox'''
        pass
    
    # hack: add "scrollmode" to user configurable options
    
    def configure(self, cnf=None, **kw):
        if not cnf is None and cnf.has_key('scrollmode'):
            self._scrollMode(cnf['scrollmode'])
            del cnf['scrollmode']
        if kw.has_key('scrollmode'):
            self._scrollMode(kw['scrollmode'])
            del kw['scrollmode']
        return Tkinter.Frame.configure(self, cnf, **kw)
    config = configure
    
    def cget(self, key):
        if key == 'scrollmode':
            return self._scrollmode
        return Tkinter.Frame.cget(self, key)
    __getitem__ = cget
    
    def keys(self):
        keys = Tkinter.Frame.keys(self) + ['scrollmode']
        keys.sort()
        return keys
    
    # methods to control the scrollbars;
    # these are mainly stolen from Pmw.ScrolledListbox
    
    def _scrollMode(self, mode):
        if mode == 'both':
            if not self._hbarOn:
                self._toggleHbar()
            if not self._vbarOn:
                self._toggleVbar()
        elif mode == 'auto':
            if self._hbarNeeded != self._hbarOn:
                self._toggleHbar()
            if self._vbarNeeded != self._vbarOn:
                self._toggleVbar()
        elif mode == 'x':
            if self._vbarOn:
                self._toggleVbar()
        elif mode == 'y':
            if self._hbarOn:
                self._toggleHbar()
        else:
            message = 'bad scrollmode option "%s": should be x, y, both or auto' % mode
            raise ValueError, message
        self._scrollmode = mode
        self._configureScrollCommands()
        
    def _configureScrollCommands(self):
        # Clean up previous scroll commands to prevent memory leak.
        tclCommandName = str(self._scrolledWidget.cget('xscrollcommand'))
        if tclCommandName != '':   
            self._scrolledWidget.deletecommand(tclCommandName)
        tclCommandName = str(self._scrolledWidget.cget('yscrollcommand'))
        if tclCommandName != '':   
            self._scrolledWidget.deletecommand(tclCommandName)
        # If both scrollmodes are not dynamic we can save a lot of
        # time by not having to create an idle job to handle the
        # scroll commands.
        if self._scrollmode == 'auto':
            self._scrolledWidget.configure(xscrollcommand=self._scrollBothLater,
                                    yscrollcommand=self._scrollBothLater)
        else:
            self._scrolledWidget.configure(xscrollcommand=self._scrollXNow,
                                    yscrollcommand=self._scrollYNow)

    def _scrollXNow(self, first, last):
        first, last = str(first), str(last)
        self.hbar.set(first, last)
        self._hbarNeeded = ((first, last) not in (('0', '1'), ('0.0', '1.0')))
        if self._scrollmode == 'auto':
            if self._hbarNeeded != self._hbarOn:
                self._toggleHbar()

    def _scrollYNow(self, first, last):
        first, last = str(first), str(last)
        self.vbar.set(first, last)
        self._vbarNeeded = ((first, last) not in (('0', '1'), ('0.0', '1.0')))
        if self._scrollmode == 'auto':
            if self._vbarNeeded != self._vbarOn:
                self._toggleVbar()

    def _scrollBothLater(self, first, last):
        # Called by the listbox to set the horizontal or vertical
        # scrollbar when it has scrolled or changed size or contents.
        if self._scrollTimer is None:
            self._scrollTimer = self.after_idle(self._scrollBothNow)

    def _scrollBothNow(self):
        # This performs the function of _scrollXNow and _scrollYNow.
        # If one is changed, the other should be updated to match.
        self._scrollTimer = None
        # Call update_idletasks to make sure that the containing frame
        # has been resized before we attempt to set the scrollbars. 
        # Otherwise the scrollbars may be mapped/unmapped continuously.
        self._scrollRecurse = self._scrollRecurse + 1
        self.update_idletasks()
        self._scrollRecurse = self._scrollRecurse - 1
        if self._scrollRecurse != 0:
            return

        xview, yview = self._scrolledWidget.xview(), self._scrolledWidget.yview()
        self.hbar.set(*xview)
        self.vbar.set(*yview)
        self._hbarNeeded = (xview != (0.0, 1.0))
        self._vbarNeeded = (yview != (0.0, 1.0))

        # If both horizontal and vertical scrollmodes are dynamic and
        # currently only one scrollbar is mapped and both should be
        # toggled, then unmap the mapped scrollbar.  This prevents a
        # continuous mapping and unmapping of the scrollbars. 
        if (self._scrollmode == 'auto' and self._hbarNeeded != self._hbarOn and
                    self._vbarNeeded != self._vbarOn and self._vbarOn != self._hbarOn):
            if self._hbarOn:
                self._toggleHbar()
            else:
                self._toggleVbar()
            return

        if self._scrollmode == 'auto':
            if self._hbarNeeded != self._hbarOn:
                self._toggleHbar()
            if self._vbarNeeded != self._vbarOn:
                self._toggleVbar()

    def _toggleHbar(self):
        self._hbarOn = not self._hbarOn
        if self._hbarOn:
            self.hbar.grid(row=1, column=0, sticky='ew')
        else:
            self.hbar.grid_forget()

    def _toggleVbar(self):
        self._vbarOn = not self._vbarOn
        if self._vbarOn:
            self.vbar.grid(row=0, column=1, sticky='ns')
        else:
            self.vbar.grid_forget()
            
    def destroy(self):
        if self._scrollTimer is not None:
            self.after_cancel(self._scrollTimer)
            self._scrollTimer = None
        Tkinter.Frame.destroy(self)
        
################################################################################
################################################################################

class ScrolledTreectrl(ScrolledWidget):
    '''Treectrl widget with one or two static or automatic scrollbars.
    Subwidgets are:
        treectrl - TkTreectrl.Treectrl widget
        hbar - horizontal Tkinter.Scrollbar
        vbar - vertical Tkinter.Scrollbar
    The widget itself is a Tkinter.Frame with one additional configuration option:
        scrollmode - may be one of "x", "y", "both" or "auto".'''
    def __init__(self, *args, **kw):
        ScrolledWidget.__init__(self, *args, **kw)
    def _setScrolledWidget(self):
        self.treectrl = Treectrl.Treectrl(self)
        return self.treectrl

################################################################################
################################################################################

class ScrolledMultiListbox(ScrolledWidget):
    '''MultiListbox widget with one or two static or automatic scrollbars.
    Subwidgets are:
        listbox - TkTreectrl.MultiListbox widget
        hbar - horizontal Tkinter.Scrollbar
        vbar - vertical Tkinter.Scrollbar
    The widget itself is a Tkinter.Frame with one additional configuration option:
        scrollmode - may be one of "x", "y", "both" or "auto".'''
    def __init__(self, *args, **kw):
        ScrolledWidget.__init__(self, *args, **kw)
    def _setScrolledWidget(self):
        self.listbox = MultiListbox.MultiListbox(self)
        return self.listbox
