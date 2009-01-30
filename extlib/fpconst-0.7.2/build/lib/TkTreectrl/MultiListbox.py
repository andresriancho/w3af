# -*- coding: iso-8859-1 -*-
'''A flexible multi column listbox widget for Tkinter.'''
from Treectrl import Treectrl

class MultiListbox(Treectrl):
    '''A flexible multi column listbox widget for Tkinter.
    Based on the Treectrl widget, it offers the following additional configuration options:
    
        columns -           a sequence of strings that defines the number of columns of the widget.
                            The strings will be used in the columnheader lines (default: (' ',)).
        command -           an optional command that will be executed when the user double-clicks
                            into the listbox or presses the Return key. The listbox index of the item
                            that was clicked on resp. of the currently active item is passed as argument
                            to the callback; if there is no item at the event coordinates resp.
                            no active item exists, this index will be -1 (default: None).
        expandcolumns -     a sequence of integers defining the columns that should expand
                            horizontally beyond the requested size when the widget is resized
                            (note that the rightmost column will always expand) (default: ()).
        selectcmd -         an optional callback that will be executed when the selection of the 
                            listbox changes. A tuple containing the indices of the currently
                            selected items as returned by curselection() will be passed to the
                            callback (default: None).
        selectbackground -  the background color to use for the selection rectangle (default: #00008B).
        selectforeground -  the foreground color to use for selected text (default: white).
    
    By default, the widget uses one pre-defined style for all columns; the widget's style()
    method allows to access and configure the default style, as well as applying new
    user-defined styles per column.
    The default style defines two elements, "text" and "select" (which describes attributes
    of the selection rectangle); these may be accessed and configured with the element() method.
    Conversion between listbox indices and treectrl item descriptors can be done with the item()
    and index() widget methods.
    Besides this, most common operations can be done with methods identical or very similar to
    those of a Tkinter.Listbox, with the exception of the selection_xxx() methods, where
    the treectrl methods are kept intact; for Tkinter.Listbox alike methods, use select_xxx().
    '''
    def __init__(self, master=None, columns=(' ',), selectcmd=None, command=None,
                 expandcolumns=(), showroot=0, selectforeground='white',
                 selectbackground='#00008B', **kw):
        Treectrl.__init__(self, master, showroot=showroot, **kw)
        self._multilistbox_opts = {'selectcmd' : selectcmd,
                                   'command' : command,
                                   'expandcolumns' : expandcolumns,
                                   'columns' : columns,
                                   'selectforeground' : selectforeground,
                                   'selectbackground' : selectbackground}
        
        self._el_text = self.element_create(type='text',
                        fill=(self._multilistbox_opts['selectforeground'], 'selected'), lines=1)
        self._el_select = self.element_create(type='rect', showfocus=1,
                            fill=(self._multilistbox_opts['selectbackground'], 'selected'))
        self._defaultstyle = self.style_create()
        self.style_elements(self._defaultstyle, self._el_select, self._el_text)
        self.style_layout(self._defaultstyle, self._el_text, padx=4, iexpand='e', expand='ns')
        self.style_layout(self._defaultstyle, self._el_select, union=(self._el_text,), ipady=1, iexpand='nsew')
        
        self._columns = []
        self._styles = []
        self.configure(columns=columns, expandcolumns=expandcolumns,
                       selectcmd=selectcmd, command=command)
        
        self.notify_bind('<Selection>', self._call_selectcmd)
        self.bind('<Double-Button-1>', self._call_command)
        self.bind('<Return>', self._call_command)
    
    ##################################################################################
    ## hackish implementation of configure() and friends for special widget options ##
    ##################################################################################
    
    def _configure_multilistbox(self, option, value):
        if option in ('selectcmd', 'command'):
            if not (value is None or callable(value)):
                raise ValueError, 'bad value for "%s" option: must be callable or None.' % option
        elif option =='selectforeground':
            self.element_configure(self._el_text, fill=(value, 'selected'))
        elif option == 'selectbackground':
            self.element_configure(self._el_select, fill=(value, 'selected'))
        elif option == 'expandcolumns':
            if not (isinstance(value, tuple) or isinstance(value, list)):
                raise ValueError, 'bad value for "expandcolumns" option: must be tuple or list.'
            # the last column should always expand
            expandcolumns = [x for x in value] + [len(self._columns) - 1]
            for column in self._columns:
                if self._columns.index(column) in expandcolumns:
                    self.column_config(column, expand=1)
                else:
                    self.column_config(column, expand=0)
        elif option == 'columns':
            # if the number of strings in value is identical with the number
            # of already existing columns, simply update the columnheader strings
            # if there are more items in value, add the missing columns
            # else remove the excess columns
            if not isinstance(value, tuple) or isinstance(value, list):
                raise ValueError, 'bad value for "columns" option: must be tuple or list.'
            if not value:
                raise ValueError, 'bad value for "columns" option: at least one column must be specified.'
            index = 0
            while index < len(value) and index < len(self._columns):
                # change title of existing columns
                self.column_config(self.column(index), text=value[index])
                index += 1
            if len(value) != len(self._columns):
                while self._columns[index:]:
                    # remove the no longer wanted columns
                    self.column_delete(self.column(index))
                    del self._columns[index]
                    del self._styles[index]
                while value[index:]:
                    # create newly requested columns
                    newcol = self.column_create(text=value[index], minwidth=35)
                    self._styles.append(self._defaultstyle)
                    self._columns.append(newcol)
                    index += 1
                # the number of columns has changed, so we need to update the
                # resize and expand options for each column and update the widget's
                # defaultstyle option
                self.configure(defaultstyle=tuple(self._styles))
                for col in self._columns[:-1]:
                    self.column_configure(col, resize=1)
                self.column_configure(self.column('end'), resize=0)
                self._configure_multilistbox('expandcolumns', self._multilistbox_opts['expandcolumns'])
        # apply the new value to the option dict
        self._multilistbox_opts[option] = value
    
    def configure(self, cnf=None, **kw):
        for opt in self._multilistbox_opts.keys():
            if not cnf is None and cnf.has_key(opt):
                self._configure_multilistbox(opt, cnf[opt])
                del cnf[opt]
            if kw.has_key(opt):
                self._configure_multilistbox(opt, kw[opt])
                del kw[opt]
        return Treectrl.configure(self, cnf, **kw)
    config = configure
    
    def cget(self, key):
        if key in self._multilistbox_opts.keys():
            return self._multilistbox_opts[key]
        return Treectrl.cget(self, key)
    __getitem__ = cget
    
    def keys(self):
        keys = Treectrl.keys(self) + self._multilistbox_opts.keys()
        keys.sort()
        return keys
    
    ########################################################################
    #       miscellaneous helper methods                                   #
    ########################################################################
    
    def _call_selectcmd(self, event):
        if self._multilistbox_opts['selectcmd']:
            sel = self.curselection()
            self._multilistbox_opts['selectcmd'](sel)
        return 'break'
    
    def _call_command(self, event):
        if self._multilistbox_opts['command']:
            if event.keysym == 'Return':
                index = self.index('active')
            else:
                index = self._event_index(event)
            self._multilistbox_opts['command'](index)
        return 'break'
    
    def _event_index(self, event):
        '''Return the listbox index where mouse event EVENT occured, or -1 if
        it occured in an empty listbox or below the last item.'''
        x, y = event.x, event.y
        xy = '@%d,%d' % (x, y)
        return self.index(xy)

    def _index2item(self, index):
        if index < 0:
            return None
        if index == 'end':
            index = self.size() - 1
        items = self.item_children('root')
        if not items:
            return None
        try:
            item = items[index]
        except IndexError:
            item = None
        return item
    
    def _item2index(self, item):
        # some treectrl methods return item descriptors as strings
        # so try to convert item into an integer first
        try:
            item = int(item)
        except ValueError:
            pass
        items = list(self.item_children('root'))
        index = -1
        if item in items:
            index = items.index(item)
        return index
    
    def _get(self, index):
        item = self._index2item(index)
        res = []
        i = 0
        for column in self._columns:
            t = self.itemelement_cget(item, column, self._el_text, 'text')
            res.append(t)
        return tuple(res)
    
    ############################################################################
    #       PUBLIC METHODS                                                     #
    ############################################################################
    
    def column(self, index):
        '''Return the column identifier for the column at INDEX.'''
        if index == 'end':
            index = len(self._columns) - 1
        return self._columns[index]
    
    def element(self, element):
        '''Return the treectrl element corresponding to ELEMENT.
        ELEMENT may be "text" or "select".'''
        if element == 'text':
            return self._el_text
        elif element == 'select':
            return self._el_select
    
    def item(self, index):
        '''Return the treectrl item descriptor for the item at INDEX.'''
        return self._index2item(index)
    
    def numcolumns(self):
        '''Return the number of listbox columns.'''
        return len(self._columns)
    
    def sort(self, column=None, element=None, first=None, last=None, mode=None,
             command=None, notreally=0):
        '''Like item_sort(), except that the item descriptor defaults to ROOT
        (which is most likely wanted) and that the FIRST and LAST options require
        listbox indices instead of treectrl item descriptors.'''
        if not first is None:
            first = self._index2item(first)
        if not last is None:
            last = self._index2item(last)
        self.item_sort('root', column, element, first, last, mode, command, notreally)
    
    def style(self, index, newstyle=None):
        '''If NEWSTYLE is specified, set the style for the column at INDEX to NEWSTYLE.
        Return the style identifier for the column at INDEX.'''
        if not newstyle is None:
            self._styles[index] = newstyle
            self.configure(defaultstyle=tuple(self._styles))
        return self._styles[index]
    
    ############################################################################
    #      Standard Listbox methods                                            #
    ############################################################################
    
    def activate(self, index):
        '''Like Tkinter.Listbox.activate(). Note that this overrides the activate()
        method inherited from Treectrl.'''
        item = self._index2item(index)
        if not item is None:
            Treectrl.activate(self, item)
    
    def bbox(self, index, column=None, element=None):
        '''Like item_bbox(), except that it requires a listbox index instead
        of a treectrl item descriptor as argument.'''
        item = self._index2item(index)
        if not item is None:
            return self.item_bbox(item, column, element)
    
    def curselection(self):
        '''Like Tkinter.Listbox.curselection().'''
        selected = self.selection_get()
        if not selected:
            return ()
        selected = list(selected)
        if 0 in selected:
            # happens if showroot == 1 and the root item is selected
            selected.remove(0)
        allitems = list(self.item_children('root'))
        sel = []
        for s in selected:
            sel.append(allitems.index(s))
        sel.sort()
        return tuple(sel)
    
    def delete(self, first, last=None):
        '''Like Tkinter.Listbox.delete() except that an additional index descriptor
        ALL may be used, so that delete(ALL) is equivalent with delete(0, END).'''
        if first == 'all':
            self.item_delete('all')
        elif (first == 0) and (last == 'end'):
            self.item_delete('all')
        elif last is None:
            self.item_delete(self._index2item(first))
        else:
            if last == 'end':
                last = self.size() - 1
            self.item_delete(self._index2item(first), self._index2item(last))
    
    def get(self, first, last=None):
        '''Like Tkinter.Listbox.get(), except that each element of the returned tuple
        is a tuple instead of a string; each of these tuples contains the text strings
        per column of a listbox item.'''
        if self.size() == 0:
            return ()
        if last is None:
            return (self._get(first),)
        if last == 'end':
            last = self.size() - 1
        res = []
        while first <= last:
            res.append(self._get(first))
            first += 1
        return tuple(res)
    
    def index(self, which=None, item=None):
        ''' Like Tkinter.Listbox.index(), except that if ITEM is specified, the
        listbox index for the treectrl item descriptor ITEM is returned. '''
        if not item is None:
            return self._item2index(item)
        items = self.item_children('root')
        if items:
            if which == 'active':
                for item in items:
                    if self.itemstate_get(item, 'active'):
                        return self._item2index(item)
            elif which == 'end':
                return self.size()
            elif isinstance(which, int):
                return which
            elif which.startswith('@'):
                which = which[1:]
                x, y = which.split(',')
                x, y = int(x.strip()), int(y.strip())
                info = self.identify(x, y)
                if info and info[0] == 'item':
                    item = info[1]
                    return self._item2index(int(item))
        return -1
    
    def insert(self, index, *args):
        '''Similar to Tkinter.Listbox.insert(), except that instead of one string
        a number of strings equal to the number of columns must be given as arguments.
        It is an error to specify more or fewer arguments than the number of columns.'''
        olditems = self.item_children('root')
        if not olditems:
            newitem = self.item_create(parent='root')[0]
        elif (index == 'end') or (index > self.size() - 1):
            newitem = self.item_create(prevsibling=olditems[-1])[0]
        else:
            newitem = self.item_create(nextsibling=olditems[index])[0]
        i = 0
        for column in self._columns:
            newtext = args[i]
            self.itemelement_config(newitem, column, self._el_text, text=newtext)
            i += 1
    
    def nearest(self, y):
        '''Like Tkinter.Listbox.nearest().'''
        size = self.size()
        # if the listbox is empty this will always return -1
        if size == 0:
            return -1
        # if there is only one item, always return 0
        elif size == 1:
            return 0
        # listbox contains two or more items, find if y hits one of them exactly;
        # if the x coord for identify() is in the border decoration, identify returns (),
        # so we cannot use x=0 here, but have to move a few pixels further
        # sometimes cget() returns TclObjects instead of strings, so do str() here first:
        x = int(str(self['borderwidth'])) + int(str(self['highlightthickness'])) + 1
        info = self.identify(x, y)
        if info and info[0] == 'item':
            return self._item2index(int(info[1]))
        # y must be above the first or below the last item
        x0, y0, x1, y1 = self.bbox(0)
        if y <= y0:
            return 0
        return size - 1
    
    def see(self, index):
        '''Like Tkinter.Listbox.see(). Note that this overrides the
        see() method inherited from Treectrl.'''
        item = self._index2item(index)
        if not item is None:
            Treectrl.see(self, item)
    
    def select_anchor(self, index=None):
        '''Like Tkinter.Listbox.select_anchor(), except that it if no INDEX is specified
        the current selection anchor will be returned.'''
        if index is None:
            anchor = self.selection_anchor()
        else:
            item = self._index2item(index)
            anchor = self.selection_anchor(item)
        if not anchor is None:
            return self._item2index(anchor)
    
    def select_clear(self, first=None, last=None):
        '''Like Tkinter.Listbox.select_clear(), except that if no arguments are
        specified, all items will be deleted, so that select_clear() is equivalent
        with select-clear(0, END).'''
        if first == 'all':
            self.selection_clear('all')
        if not first is None:
            first = self._index2item(first)
        if not last is None:
            last = self._index2item(last)
        self.selection_clear(first, last)
    
    def select_includes(self, index):
        '''Like Tkinter.Listbox.select_includes().'''
        item = self._index2item(index)
        if not item is None:
            return self.selection_includes(item)
        return 0
    
    def select_set(self, first, last=None):
        '''Like Tkinter.Listbox.select_set().'''
        if first == 'all':
            self.selection_modify(select='all')
        elif (first == 0) and (last == 'end'):
            self.selection_modify(select='all')
        elif last is None:
            self.selection_modify(select=(self._index2item(first),))
        else:
            if last == 'end':
                last = self.size() - 1
            newsel = self.item_children('root')[first:last+1]
            self.selection_modify(select=newsel)
    
    def size(self):
        '''Like Tkinter.Listbox.size().'''
        return len(self.item_children('root'))
