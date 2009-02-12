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
import  traceback, webbrowser
import gtk
from core.controllers.w3afException import w3afException

# w3af crash File creation
import tempfile
from core.data.fuzzer.fuzzer import createRandAlNum
import os
import cgi
import time
import md5
import urllib2, urllib
import cookielib
from core.controllers.misc.get_w3af_version import get_w3af_version
import core.data.url.handlers.MultipartPostHandler as MultipartPostHandler


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

class bug_report_result(gtk.Window):
    def __init__(self, text, url):
        super(bug_report_result,self).__init__(type=gtk.WINDOW_TOPLEVEL)
        
        # Save for later
        self.url = url
        self.text = text
        
        self.set_modal(True)
        self.set_title('Bug report failed!')
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.vbox = gtk.VBox()
        
        self.label = gtk.Label()
        self.label.set_line_wrap(True)
        self.label.set_selectable(True)
        
        
        # The label text
        self.label.set_markup( text )
        
        self.label.show()
        self.vbox.pack_start(self.label, True, False)
        
        # The link
        link = gtk.EventBox()
        link.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        link_label_text = '\n<u><span foreground="#0000AA">'
        link_label_text += cgi.escape(url)+'</span></u>\n'
        linkLabel = gtk.Label( link_label_text )
        linkLabel.set_line_wrap(True)
        linkLabel.set_use_markup( True )
        link.add( linkLabel )
        link.connect( 'button_press_event', self.on_link_clicked )
        link.show_all()
        self.vbox.pack_start(link)
        
        # Close button
        self.butt_close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.butt_close.connect("clicked", self._handle_cancel )
        self.vbox.pack_start(self.butt_close, True, False)
        
        self.add(self.vbox)
        self.show_all()
        
        # This is a quick fix to get around the problem generated by "set_selectable"
        # that selects the text by default
        self.label.select_region(0, 0)
      
    def on_link_clicked(self, widg, evt):
        webbrowser.open( self.url )
        
    def run(self):
        while True:
            time.sleep(0.1)
            while gtk.events_pending():
                gtk.main_iteration()
    
    def _handle_cancel(self, widg):
        # Exit w3af
        endThreads()
        gtk.main_quit()
        sys.exit(-1) 

class bug_report_window(gtk.Window):
    def __init__(self, title, exception_text, w3af_version, filename):
        super(bug_report_window,self).__init__(type=gtk.WINDOW_TOPLEVEL)
        
        # Set generic window settings
        self.set_modal(True)
        self.set_title(title)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.connect("delete_event", gtk.main_quit)
        self.vbox = gtk.VBox()
        
        # Internal variables
        self.bug_url = None
        self.manual_bug_report = 'https://sourceforge.net/tracker2/?func=add&group_id=170274&atid=853652'
        
        # Save the info for later
        self.exception_text = exception_text
        self.w3af_version = w3af_version
        self.filename = filename
        
        # the textview inside scrollbars
        self.label = gtk.Label()
        self.label.set_line_wrap(True)
        self.label.set_selectable(True)
        
        label_text = _('\n<b>An unhandled exception was raised:</b>\n\n')
        exception_text = cgi.escape(exception_text)
        label_text += exception_text + '\n'
        label_text += _("<i>All this info is in a file called ") + filename + _(" for later review.</i>\n\n")
        label_text += _('If you wish, <b>you can contribute</b> to the w3af project and submit this')
        label_text += _(' bug to the sourceforge bug tracking system from within this window.')
        label_text += _(' Please click "Ok" to contribute, or "Cancel" to exit w3af.\n\n')
        label_text += _('w3af will only send the exception traceback and the version information to')
        label_text += _(' sourceforge, no personal or confidencial information is collected.\n')
    
        self.label.set_markup( label_text )
        self.label.show()
        
        self.vbox.pack_start(self.label, True, False)
        
        # the buttons
        self.hbox = gtk.HBox()
        self.butt_send = gtk.Button(stock=gtk.STOCK_OK)
        self.butt_send.connect("clicked", self._handle_send )
        self.hbox.pack_start(self.butt_send, True, False)
        
        self.butt_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.butt_cancel.connect("clicked", self._handle_cancel )
        self.hbox.pack_start(self.butt_cancel, True, False)
        self.vbox.pack_start(self.hbox, True, False)
        
        # Init urllib2 handlers
        self._init_urllib2_handlers()
        
        #self.resize(400,450)
        self.add(self.vbox)
        self.show_all()
        
        # This is a quick fix to get around the problem generated by "set_selectable"
        # that selects the text by default
        self.label.select_region(0, 0)
        
    def _init_urllib2_handlers(self):
        # Build the cookie handler
        cj = cookielib.LWPCookieJar()
        cookie_handler = urllib2.HTTPCookieProcessor(cj)
        
        # Build the multipart post handler
        multi_handler = MultipartPostHandler.MultipartPostHandler()
        
        opener = apply(urllib2.build_opener, (multi_handler,cookie_handler) )
        urllib2.install_opener(opener)

    def run(self):
        while True:
            time.sleep(0.1)
            while gtk.events_pending():
                gtk.main_iteration()

    def _handle_cancel(self, widg):
        # Exit w3af
        endThreads()
        gtk.main_quit()
        sys.exit(-1)

    def _login_to_sf(self, user, passwd):
        '''
        Perform a login to the sourceforge page using the provided user and password.
        
        @parameter user: The user
        @parameter passwd: The password
        @return: True if successful login, false otherwise.
        '''
        url = 'https://sourceforge.net/account/login.php'
        values = {'return_to' : '',
            'ssl_status' : '',
            'form_loginname' : user, 
            'form_pw' : passwd,
            'login' : 'Log in'}

        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        try:
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            return False
        else:
            return 'Invalid username or password' not in the_page

    def _ask_bug_information(self):
        '''
        @return: A tuple with the bug title and the bug description provided by the user.
        '''
        default_text = '''What steps will reproduce the problem?
1. 
2. 
3. 

What is the expected output? What do you see instead?


What operating system are you using?


Please provide any additional information below:


'''
        #base this on a message dialog
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK,
            None)
        dialog.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        
        
        msg = '<b>Step 1 of 2</b>\n\n\n'
        msg += 'Please provide the following information about the bug:\n'
        dialog.set_markup( msg )
        
        #create the text input field
        summary_entry = gtk.Entry()
        
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        description_text_view = gtk.TextView()
        buffer = description_text_view.get_buffer()
        buffer.set_text(default_text)
        sw.add(description_text_view)
        
        #create a horizontal box to pack the entry and a label
        summary_hbox = gtk.HBox()
        summary_hbox.pack_start(gtk.Label("Summary:  "), False, 5, 5)
        summary_hbox.pack_end(summary_entry)
        
        description_hbox = gtk.HBox()
        description_hbox.pack_start(gtk.Label("Description:"), False, 5, 5)
        description_hbox.pack_start(sw, True, True, 0)
        
        #add it and show it
        dialog.vbox.pack_start(summary_hbox, True, True, 0)
        dialog.vbox.pack_start(description_hbox, True, True, 0)
        dialog.show_all()
        
        #go go go
        dialog.run()
        summary = summary_entry.get_text()
        description = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        dialog.destroy()
        
        return summary, description
        

    def _handle_send(self, widg):
        '''
        Handle the Ok button click.
        '''
        # Ask for a bug title and description
        summary, description = self._ask_bug_information()
        
        invalid_login = False
        while True:
            # Ask for user and password, or anonymous
            user, password = self._ask_user_password( invalid_login )
        
            if user == password == '':
                # anonymous bug report, no login.
                login_ok = True
            else:
                # Login to sourceforge
                login_ok = self._login_to_sf( user, password )
                invalid_login = True
            
            if login_ok:
                break
        
        if self._report_bug(summary, description):
            # Show the tracking URL to the user
            text = _('<b>Thanks for reporting your bugs!</b>\n\n')
            text += _('You can track your bug report here:\n')
            brf = bug_report_result(text, self.bug_url)
        else:
            # bug report failed
            label_text = _('<b>The bug report failed!</b>\n\n')
            label_text += _('Please try to report this bug manually submitting the information')
            label_text += _(' contained inside the <i>'+self.filename+'</i> file here: ')
            brf = bug_report_result(label_text, self.manual_bug_report)
            
        brf.run()
            
    def _ask_user_password(self, invalid_login=False):
        '''
        @return: A tuple with the user and the password to use. Blank in both if anonymous.
        '''
        #base this on a message dialog
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK,
            None)
        dialog.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        
        
        msg = '<b>Step 2 of 2</b>\n\n\n'
        if invalid_login:
            msg += '<b><i>Your credentials are invalid, please try again.</i></b>\n\n'
            
        msg += 'Please enter your <b>sourceforge credentials</b> or leave both'
        msg += ' text entries <i>blank if you want to report the bug <b>anonymously</b></i>.'
        dialog.set_markup( msg )
        
        #create the text input field
        user_entry = gtk.Entry()
        user_entry.connect("activate", lambda x: dialog.response(gtk.RESPONSE_OK))  
        passwd_entry = gtk.Entry()
        passwd_entry.connect("activate", lambda x: dialog.response(gtk.RESPONSE_OK) )
        passwd_entry.set_visibility(False)
        
        #create a horizontal box to pack the entry and a label
        user_hbox = gtk.HBox()
        user_hbox.pack_start(gtk.Label("Username:"), False, 5, 5)
        user_hbox.pack_end(user_entry)
        
        passwd_hbox = gtk.HBox()
        passwd_hbox.pack_start(gtk.Label("Password:  "), False, 5, 5)
        passwd_hbox.pack_end(passwd_entry)
        
        #some secondary text
        warning = "Your credentials won't be stored in your computer, and"
        warning += " will only be sent over secure HTTPS connections."
        dialog.format_secondary_markup( warning )
        
        #add it and show it
        dialog.vbox.pack_start(user_hbox, True, True, 0)
        dialog.vbox.pack_start(passwd_hbox, True, True, 0)
        dialog.show_all()
        
        #go go go
        dialog.run()
        user = user_entry.get_text()
        passwd = passwd_entry.get_text()
        dialog.destroy()
        
        return user, passwd
    
    def on_link_clicked(self, widg, other):
        '''
        Go to the bug URL.
        '''
        if self.bug_url:
            webbrowser.open( self.bug_url )
        else:
            webbrowser.open( self.manual_bug_report )
    
    def _report_bug(self, user_title, user_description):
        '''
        I use urllib2 instead of the w3af wrapper, because the error may be in there!
        
        @parameter user_title: The title that the user wants to use in the bug report
        @parameter user_description: The description for the bug that was provided by the user
        @return: True if the bug report was successful
        '''
        
        # Handle the summary
        summary = '[Auto-Generated] Bug Report - '
        if user_title:
            summary += user_title
        else:
            # Generate the summary, the random token is added to avoid the
            # double click protection added by sourceforge.
            summary += md5.new( time.ctime() ).hexdigest()
            
        # Now we handle the details
        details = ''
        if user_description:
            details += 'User description: \n'+ user_description + '\n\n\n'
        
        details += 'Version information: \n' + self.w3af_version + '\n\n\n'
        details += 'Traceback: \n' + self.exception_text
        
        url = 'https://sourceforge.net/tracker2/index.php'
        values = {'group_id' : '170274',
            'atid' : '853652',
            'func' : 'postadd', 
            'category_id':'1166485', 
            'artifact_group_id':'100', 
            'assigned_to':'100', 
            'priority':'5',
            'summary': summary,
            'details': details,
            'input_file': file(self.filename),
            'file_description':'',
            'submit':'Add Artifact' }

        req = urllib2.Request(url, values)
        try:
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            return False
        
        if 'ERROR' not in the_page:
            # parse the tracking URL
            # (Artifact <a href="/tracker2/?func=detail&aid=2590539&group_id=170274&atid=853652">2590539</a>)
            re_result = re.findall('\\(Artifact <a href="(.*?)">\d*</a>\\)', the_page)
            if re_result:
                self.bug_url = 'https://sourceforge.net' + re_result[0]
            return True
        else:
            return False

def _crash(type, value, tb):
    '''Function to handle any exception that is not addressed explicitly.'''
    if issubclass(type, KeyboardInterrupt ):
        endThreads()
        import core.controllers.outputManager as om
        om.out.console(_('Thanks for using w3af.'))
        om.out.console(_('Bye!'))
        sys.exit(0)
        return
        
    exception = traceback.format_exception(type, value, tb)
    exception = "".join(exception)
    print exception

    # get version info for python, gtk and pygtk
    versions = _("\nPython version:\n%s\n\n") % sys.version
    versions += _("GTK version:%s\n") % ".".join(str(x) for x in gtk.gtk_version)
    versions += _("PyGTK version:%s\n\n") % ".".join(str(x) for x in gtk.pygtk_version)

    # get the version info for w3af
    versions += '\n' + get_w3af_version()

    # save the info to a file
    filename = tempfile.gettempdir() + os.path.sep + "w3af_crash-" + createRandAlNum(5) + ".txt"
    arch = file(filename, "w")
    arch.write(_('Submit this bug here: https://sourceforge.net/tracker/?func=add&group_id=170274&atid=853652 \n'))
    arch.write(versions)
    arch.write(exception)
    arch.close()
    
    # Create the dialog that allows the user to send the bug to sourceforge
    
    bug_report_win = bug_report_window(_('Bug detected!'), exception, versions, filename)
    
    # Blocks waiting for user interaction
    bug_report_win.run()
    
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
            

def loadImage(filename):
    '''Loads a pixbuf from disk.

    @param filename: the file name, full path
    @returns: The pixbuf from the image.
    '''
    im = gtk.Image()
    im.set_from_file(filename)
    im.show()
    return im


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
    ("info", None): loadImage('core/ui/gtkUi/data/information.png'),
    ("vuln", None):  loadImage('core/ui/gtkUi/data/vulnerability.png'),
    ("shell", None):  loadImage('core/ui/gtkUi/data/shell.png'),
    ("vuln", severity.LOW):  loadImage('core/ui/gtkUi/data/vulnerability_l.png'),
    ("vuln", severity.MEDIUM):  loadImage('core/ui/gtkUi/data/vulnerability_m.png'),
    ("vuln", severity.HIGH):  loadImage('core/ui/gtkUi/data/vulnerability_h.png'),
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
    helpfile = os.path.join(os.getcwd(), "readme/gtkUiHTML/gtkUiUsersGuide.html" + chapter)
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
