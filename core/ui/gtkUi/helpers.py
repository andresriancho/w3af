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

import threading, re, sys, Queue
import  traceback
import gtk
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
    dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, message)
    dlg.run()
    dlg.destroy()
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

def _crash(type, value, tb):
    '''Function to handle any exception that is not addressed explicitly.'''
    if issubclass(type, KeyboardInterrupt ):
        endThreads()
        import core.controllers.outputManager as om
        om.out.console('Thanks for using w3af.')
        om.out.console('Bye!')
        sys.exit(0)
        return
        
    exception = traceback.format_exception(type, value, tb)
    exception = "".join(exception)
    print exception

    # get version info
    versions = "\nPython version:\n%s\n\n" % sys.version
    versions += "GTK version:%s\n" % ".".join(str(x) for x in gtk.gtk_version)
    versions += "PyGTK version:%s\n\n" % ".".join(str(x) for x in gtk.pygtk_version)

    # save the info to a file
    # FIXME: What if I can't create the file ?
    arch = file("w3af_crash.txt", "w")
    arch.write('Submit this bug here: https://sourceforge.net/tracker/?func=add&group_id=170274&atid=853652 \n')
    arch.write(versions)
    arch.write(exception)
    arch.close()

    # inform the user
    exception += "\nAll this info is in a file called w3af_crash.txt for later review. Please report this bug here https://sourceforge.net/tracker/?func=add&group_id=170274&atid=853652 (this URL is also printed in the file), thank you!"
    exception += "\n\nThe program will exit after you close this window."
    dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, exception)
    dlg.set_title('Bug detected!')
    dlg.run()
    dlg.destroy()
    endThreads()
    gtk.main_quit()
    sys.exit(-1)
    
sys.excepthook = _crash


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

    def get(self):
        '''Serves the elements taken from the queue.'''
        idx = 0
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
            
class StatusBar(gtk.Statusbar):
    '''All status bar functionality.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, initmsg=None):
        super(StatusBar,self).__init__()
        self._context = self.get_context_id("unique_sb")
        self.show()
        self._timer = None

        if initmsg is not None:
            self.__call__(initmsg)
        
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
        

def loadPixbuf(filename):
    '''Loads a pixbuf from disk.

    @param filename: the file name, full path
    @returns: The pixbuf from the image.
    '''
    im = gtk.Image()
    im.set_from_file(filename)
    im.show()
    return im.get_pixbuf()


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
    ("info", None): loadPixbuf('core/ui/gtkUi/data/information.png'),
    ("vuln", severity.LOW):  loadPixbuf('core/ui/gtkUi/data/vulnerability_l.png'),
    ("vuln", severity.MEDIUM):  loadPixbuf('core/ui/gtkUi/data/vulnerability_m.png'),
    ("vuln", severity.HIGH):  loadPixbuf('core/ui/gtkUi/data/vulnerability_h.png'),
}
KB_COLOR_LEVEL = {
    ("info", None):            0,
    ("vuln", severity.LOW):    1,
    ("vuln", severity.MEDIUM): 2,
    ("vuln", severity.HIGH):   3,
}

KB_COLORS = ["black", "orange", "red", "red"]

