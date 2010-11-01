'''
helpers.py

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

# This module is a collection of useful code snippets for the GTK gui

import threading, re, Queue
import  webbrowser
import gtk
import os
from core.controllers.w3afException import w3afException

RE_TRIM_SPACES = re.compile( "([\w.]) {1,}")


def all(iterable):
    '''Redefinition of >=2.5 builtin all().
    
    @param iterable: a collection of somethings.
    @return: True if bool(x) is True for all values x in the iterable.

    @author: Taken from Python docs

    '''
    for element in iterable:
        if not element:
            return False
    return True

def any(iterable):
    '''Redefinition of >=2.5 builtin all().
    
    @param iterable: a collection of somethings.
    @return: Return True if any element of the iterable is true

    @author: Taken from Python docs
    '''
    for element in iterable:
        if element:
            return True
    return False

class PropagateBuffer(object):
    '''Buffer to don't propagate signals when it's not necessary.

    @param target: the target to alert when the change *is* propagated.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, target):
        self.target = target
        self.alerted = {}
        self.last_notified = None

    def change(self, widg, status):
        '''A change enters the buffer.

        @param widg: the widget that changed
        @param status: the new status of the widget
        '''
        # if the widget didn't change anything, we do not propagate
        if self.alerted.get(widg) == status:
            return
        
        # something changed, let's see our message
        self.alerted[widg] = status
        message = all(self.alerted.values())

        # save and propagate if different
        if message != self.last_notified:
            self.last_notified = message
            self.target(message)
        return


class PropagateBufferPayload(object):
    '''Equal to PropagateBuffer, but sending a payload

    @param target: the target to alert when the change *is* propagated.
    @param payload: anything to transmit

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, target, *payload):
        self.target = target
        self.alerted = {}
        self.last_notified = None
        self.payload = payload

    def change(self, widg, status):
        '''A change enters the buffer.

        @param widg: the widget that changed
        @param status: the new status of the widget
        '''
        # if the widget didn't change anything, we do not propagate
        if self.alerted.get(widg) == status:
            return
        
        # something changed, let's see our message
        self.alerted[widg] = status
        message = all(self.alerted.values())

        # save and propagate if different
        if message != self.last_notified:
            self.last_notified = message
            self.target(message, *self.payload)
        return


def cleanDescription(desc):
    '''Cleans a description.

    Normally a plugin generates these descriptions with a lot of
    spaces at the beggining of each line; this function tries to
    eliminate all these spaces.

    Also trims more than one space between words.
    
    @param desc: the description to clean
    @return The cleaned description

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    # convert spaces to tabs, and all to lines
    desc = desc.expandtabs(4)
    desc = desc.splitlines()

    # find indentation of first line used
    firstline = 0
    while len(desc[firstline].strip()) == 0:
        firstline += 1
    initialindent = 0
    while desc[firstline][initialindent] == " ":
        initialindent += 1
        
    # strip initial indentation if it's all spaces
    lines = []
    for lin in desc:
        indent = lin[:initialindent]
        if indent == " "*len(indent):
            lines.append(lin[initialindent:])

    desc = "\n".join(lines)

    # trim spaces
    desc = RE_TRIM_SPACES.sub("\\1 ", desc)

    return desc



#-- the following are for thread handling

_threadPool = []

def endThreads():
    '''This function must be called once when the GUI shuts down'''
    for t in _threadPool:
        if not t.isAlive():
            continue
        t.my_thread_ended = True
        t.join()

class RegistThread(threading.Thread):
    '''Class to provide registered threads.
    
    If the class that inherits this will get locked listening a queue, it
    should pass it here, at thread termination it will receive there a
    'Terminated' message.

    The inheriting class will need to implement the main loop in a run()
    method; the start() call is automatic. 

    It must supervise if needs to finish through the 'self.my_thread_ended'
    bool attribute.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        _threadPool.append(self)
        self.my_thread_ended = False
        super(RegistThread,self).__init__()
        self.start()

#--

#-- the following is for core wrapping

def friendlyException(message):
    '''Creates the dialog showing the message.

    @param message: text received in the friendly exception.
    '''
    class w3af_message_dialog(gtk.MessageDialog):
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
            
    dlg = w3af_message_dialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, message)
    dlg.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
    dlg.dialog_run()
    return

class _Wrapper(object):
    '''Wraps a call to the Core.

    If the core raises a friendly exception, it's not propagated but
    shown the message in a pop up.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, friendly):
        self.friendly = friendly

    def __call__(self, func, *args, **kwargs):
        '''Apply the wrap.'''
        try:
            return func(*args, **kwargs)
        except Exception, err:
            if isinstance(err, self.friendly):
                friendlyException(str(err))
            raise

coreWrap = _Wrapper(w3afException)

#--
# Trying to not use threads anymore, but still need to 
# supervise queues


class IteratedQueue(RegistThread):
    '''Transform a Queue into a generator.

    The queue is supervised inside a thread, and all the elements are
    taken and stored in a internal list; these elements can be consulted
    iterating .get().

    Multiple iterations are supported simultaneously.

    @param queue: The queue to supervise.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, queue):
        self.inputqueue = queue
        self.repository = []
        RegistThread.__init__(self)

    def run(self):
        '''The initial function of the thread.'''
        while not self.my_thread_ended:
            try:
                msg = self.inputqueue.get(timeout=1)
            except Queue.Empty:
                pass
            else:
                self.repository.append(msg)

    def get(self, start_idx=0):
        '''Serves the elements taken from the queue.'''
        if start_idx > len(self.repository):
            start_idx = len(self.repository)
            
        idx = start_idx
        
        while True:
            if idx == len(self.repository):
                msg = None
            else:
                msg = self.repository[idx]
                idx += 1
            yield msg


class BroadcastWrapper(object):
    '''Broadcast methods access to several widgets.
    
    Wraps objects to be able to have n widgets, and handle them
    as one.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, *values):
        self.initvalues = values
        self.widgets = []
    
    def __addWidget(self, widg):
        '''Adds the widget to broadcast.'''
        self.widgets.append(widg)

    def __getattr__(self, attr):
        if attr == "addWidget":
            return self.__addWidget

        def call(*args, **kwargs):
            for w in self.widgets:
                realmeth = getattr(w, attr)
                realmeth(*args, **kwargs)
        return call

# This is a helper for debug, you just should connect the
# 'event' event to this debugHandler

event_types = [i for i in vars(gtk.gdk).values() if type(i) is gtk.gdk.EventType]

def debugHandler(widget, event, *a):
    '''Just connect it to the 'event' event.'''
    if event.type in event_types:
        print event.type.value_nick

class Throbber(gtk.ToolButton):
    '''Creates the throbber widget.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        self.img_static = gtk.Image()
        self.img_static.set_from_file('core/ui/gtkUi/data/throbber_static.gif')
        self.img_static.show()
        self.img_animat = gtk.Image()
        self.img_animat.set_from_file('core/ui/gtkUi/data/throbber_animat.gif')
        self.img_animat.show()

        super(Throbber,self).__init__(self.img_static, "")
        self.set_sensitive(False)
        self.show()

    def running(self, spin):
        '''Returns if running.'''
        if spin:
            self.set_icon_widget(self.img_animat)
        else:
            self.set_icon_widget(self.img_static)
            

def loadImage(filename, path='core/ui/gtkUi/data/'):
    '''Loads a pixbuf from disk.

    @param filename: the file name, full path
    @returns: The pixbuf from the image.
    '''
    im = gtk.Image()
    filename = os.path.join(path, filename)
    im.set_from_file(filename)
    im.show()
    return im



def loadIcon(stock_item_id):
    '''Loads a pixbuf from Stock. 
    
    @param stock_item_id: Stock item id string
    @return: The icon's pixbuf
    '''
    # If param id not found use default stock item.
    stock_item = getattr(gtk, stock_item_id, gtk.STOCK_MISSING_IMAGE)
    icon_theme = gtk.IconTheme()
    try:
        icon = icon_theme.load_icon(stock_item, 16, ())
    except:
        icon = loadImage('missing-image.png').get_pixbuf()
    return icon


class SensitiveAnd(object):
    ''''AND's some sensitive info for a widget.
    
    If all says it should be enable it is. If only one says it shouldn't
    it's off.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, target, falseDefaults=None):
        if falseDefaults is None:
            falseDefaults = []
        self.target = target
        self.opinions = dict.fromkeys(falseDefaults, False)

    def set_sensitive(self, how, whosays=None):
        '''Sets the sensitivity of the target.'''
        self.opinions[whosays] = how
        sensit = all(self.opinions.values())
        self.target.set_sensitive(sensit)
            
        
import core.data.constants.severity as severity
KB_ICONS = {
    ("info", None): loadImage('information.png'),
    ("vuln", None):  loadImage('vulnerability.png'),
    ("shell", None):  loadImage('shell.png'),
    ("vuln", severity.LOW):  loadImage('vulnerability_l.png'),
    ("vuln", severity.MEDIUM):  loadImage('vulnerability_m.png'),
    ("vuln", severity.HIGH):  loadImage('vulnerability_h.png'),
}
KB_COLOR_LEVEL = {
    ("info", None):            0,
    ("vuln", severity.LOW):    1,
    ("vuln", severity.MEDIUM): 2,
    ("vuln", severity.HIGH):   3,
}

KB_COLORS = ["black", "orange", "red", "red"]


def open_help(chapter=''):
    '''Opens the help file in user's preferred browser.

    @param chapter: the chapter of the help, optional.
    '''
    if chapter:
        chapter = '#' + chapter
    helpfile = os.path.join(os.getcwd(), "readme/EN/gtkUiHTML/gtkUiUsersGuide.html" + chapter)
    webbrowser.open("file://" + helpfile)


def write_console_messages( dlg ):
    '''
    Write console messages to the TextDialog.
    
    @parameter dlg: The TextDialog.
    '''
    import core.data.kb.knowledgeBase as kb
    from . import messages
    
    msg_queue = messages.getQueueDiverter()
    get_message_index = kb.kb.getData('get_message_index', 'get_message_index')
    inc_message_index = kb.kb.getData('inc_message_index', 'inc_message_index')
    
    for msg in msg_queue.get(get_message_index()):
        if msg is None:
            yield True
            continue
        
        inc_message_index()

        if msg.getType() != 'console':
            continue

        # Handling new lines
        text = msg.getMsg()
        if msg.getNewLine():
            text += '\n'

        dlg.addMessage( text )

    yield False
