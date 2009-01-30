# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2003-2006 Gary Bishop.
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
''' an attempt to implement readline for Python in Python using ctypes'''
import sys,os,re
from glob import glob

import clipboard,logger,console
from   logger import log,log_sock
from error import ReadlineError,GetSetError
from   pyreadline.keysyms.common import make_KeyPress_from_keydescr

import pyreadline.lineeditor.lineobj as lineobj
import pyreadline.lineeditor.history as history
import release

from modes import editingmodes

in_ironpython="IronPython" in sys.version
if in_ironpython:#ironpython does not provide a prompt string to readline
    import System    
    default_prompt=">>> "
else:
    default_prompt=""
    import pdb


def quote_char(c):
    if ord(c)>0:
        return c

def inword(buffer,point):
    return buffer[point:point+1] in [A-Za-z0-9]


class Readline(object):
    def __init__(self):
        self.startup_hook = None
        self.pre_input_hook = None
        self.completer = None
        self.completer_delims = " \t\n\"\\'`@$><=;|&{("
        self.console = console.Console()
        self.size = self.console.size()
        self.prompt_color = None
        self.command_color = None
        self.selection_color = self.console.saveattr<<4
        self.key_dispatch = {}
        self.previous_func = None
        self.first_prompt = True
        self.next_meta = False # True to force meta on next character
        self.tabstop = 4
        self.allow_ctrl_c=False
        self.ctrl_c_tap_time_interval=0.3
        self.debug=False

        self.begidx = 0
        self.endidx = 0

        # variables you can control with parse_and_bind
        self.show_all_if_ambiguous = 'off'
        self.mark_directories = 'on'
        self.bell_style = 'none'
        self.mark=-1
        self.l_buffer=lineobj.ReadLineTextBuffer("")
        self._history=history.LineHistory()

        # this code needs to follow l_buffer and history creation
        self.editingmodes=[mode(self) for mode in editingmodes]
        for mode in self.editingmodes:
            mode.init_editing_mode(None)
        self.mode=self.editingmodes[0]

        self.read_inputrc()
        log("\n".join(self.rl_settings_to_string()))

        #Paste settings    
        #assumes data on clipboard is path if shorter than 300 characters and doesn't contain \t or \n
        #and replace \ with / for easier use in ipython
        self.enable_ipython_paste_for_paths=True

        #automatically convert tabseparated data to list of lists or array constructors
        self.enable_ipython_paste_list_of_lists=True
        self.enable_win32_clipboard=True

        self.paste_line_buffer=[]

    #Below is for refactoring, raise errors when using old style attributes 
    #that should be refactored out
    def _g(x):
        def g(self):
            raise GetSetError("GET %s"%x)
        def s(self,q):
            raise GetSetError("SET %s"%x)
        return g,s
    line_buffer=property(*_g("line_buffer"))
    line_cursor=property(*_g("line_buffer"))
    undo_stack =property(*_g("undo_stack")) # each entry is a tuple with cursor_position and line_text
    history_length =property(*_g("history_length")) # each entry is a tuple with cursor_position and line_text
    history =property(*_g("history")) # each entry is a tuple with cursor_position and line_text
    history_cursor =property(*_g("history_cursor")) # each entry is a tuple with cursor_position and line_text


#  To export as readline interface

    def parse_and_bind(self, string):
        '''Parse and execute single line of a readline init file.'''
        try:
            log('parse_and_bind("%s")' % string)
            if string.startswith('#'):
                return
            if string.startswith('set'):
                m = re.compile(r'set\s+([-a-zA-Z0-9]+)\s+(.+)\s*$').match(string)
                if m:
                    var_name = m.group(1)
                    val = m.group(2)
                    try:
                        setattr(self, var_name.replace('-','_'), val)
                    except AttributeError:
                        log('unknown var="%s" val="%s"' % (var_name, val))
                else:
                    log('bad set "%s"' % string)
                return
            m = re.compile(r'\s*(.+)\s*:\s*([-a-zA-Z]+)\s*$').match(string)
            if m:
                key = m.group(1)
                func_name = m.group(2)
                py_name = func_name.replace('-', '_')
                try:
                    func = getattr(self.mode, py_name)
                except AttributeError:
                    log('unknown func key="%s" func="%s"' % (key, func_name))
                    if self.debug:
                        print 'pyreadline parse_and_bind error, unknown function to bind: "%s"' % func_name
                    return
                self.mode._bind_key(key, func)
        except:
            log('error')
            raise

    def get_line_buffer(self):
        '''Return the current contents of the line buffer.'''
        return self.l_buffer.get_line_text()

    def insert_text(self, string):
        '''Insert text into the command line.'''
        self.l_buffer.insert_text(string)
        
    def read_init_file(self, filename=None): 
        '''Parse a readline initialization file. The default filename is the last filename used.'''
        log('read_init_file("%s")' % filename)

    #History file book keeping methods (non-bindable)
    
    def add_history(self, line):
        '''Append a line to the history buffer, as if it was the last line typed.'''
        self._history.add_history(line)

    def get_history_length(self ):
        '''Return the desired length of the history file.

        Negative values imply unlimited history file size.'''
        return self._history.get_history_length()

    def set_history_length(self, length): 
        '''Set the number of lines to save in the history file.

        write_history_file() uses this value to truncate the history file
        when saving. Negative values imply unlimited history file size.
        '''
        self._history.set_history_length(length)

    def clear_history(self):
        '''Clear readline history'''
        self._history.clear_history()

    def read_history_file(self, filename=None): 
        '''Load a readline history file. The default filename is ~/.history.'''
        self._history.read_history_file(filename)

    def write_history_file(self, filename=None): 
        '''Save a readline history file. The default filename is ~/.history.'''
        self._history.write_history_file(filename)

    #Completer functions

    def set_completer(self, function=None): 
        '''Set or remove the completer function.

        If function is specified, it will be used as the new completer
        function; if omitted or None, any completer function already
        installed is removed. The completer function is called as
        function(text, state), for state in 0, 1, 2, ..., until it returns a
        non-string value. It should return the next possible completion
        starting with text.
        '''
        log('set_completer')
        self.completer = function

    def get_completer(self): 
        '''Get the completer function. 
        ''' 

        log('get_completer') 
        return self.completer 

    def get_begidx(self):
        '''Get the beginning index of the readline tab-completion scope.'''
        return self.begidx

    def get_endidx(self):
        '''Get the ending index of the readline tab-completion scope.'''
        return self.endidx

    def set_completer_delims(self, string):
        '''Set the readline word delimiters for tab-completion.'''
        self.completer_delims = string

    def get_completer_delims(self):
        '''Get the readline word delimiters for tab-completion.'''
        return self.completer_delims

    def set_startup_hook(self, function=None): 
        '''Set or remove the startup_hook function.

        If function is specified, it will be used as the new startup_hook
        function; if omitted or None, any hook function already installed is
        removed. The startup_hook function is called with no arguments just
        before readline prints the first prompt.

        '''
        self.startup_hook = function

    def set_pre_input_hook(self, function=None):
        '''Set or remove the pre_input_hook function.

        If function is specified, it will be used as the new pre_input_hook
        function; if omitted or None, any hook function already installed is
        removed. The pre_input_hook function is called with no arguments
        after the first prompt has been printed and just before readline
        starts reading input characters.

        '''
        self.pre_input_hook = function

##  Internal functions

    def rl_settings_to_string(self):
        out=["%-20s: %s"%("show all if ambigous",self.show_all_if_ambiguous)]
        out.append("%-20s: %s"%("mark_directories",self.mark_directories))
        out.append("%-20s: %s"%("bell_style",self.bell_style))
        out.append("%-20s: %s"%("mark_directories",self.mark_directories))
        out.append("------------- key bindings ------------")
        tablepat="%-7s %-7s %-7s %-15s %-15s "
        out.append(tablepat%("Control","Meta","Shift","Keycode/char","Function"))
        bindings=[(k[0],k[1],k[2],k[3],v.__name__) for k,v in self.mode.key_dispatch.iteritems()]
        bindings.sort()
        for key in bindings:
            out.append(tablepat%(key))
        return out
    
    def _bell(self):
        '''ring the bell if requested.'''
        if self.bell_style == 'none':
            pass
        elif self.bell_style == 'visible':
            raise NotImplementedError("Bellstyle visible is not implemented yet.")
        elif self.bell_style == 'audible':
            self.console.bell()
        else:
            raise ReadlineError("Bellstyle %s unknown."%self.bell_style)

    def _clear_after(self):
        c = self.console
        x, y = c.pos()
        w, h = c.size()
        c.rectangle((x, y, w+1, y+1))
        c.rectangle((0, y+1, w, min(y+3,h)))

    def _set_cursor(self):
        c = self.console
        xc, yc = self.prompt_end_pos
        w, h = c.size()
        xc += self.l_buffer.visible_line_width()
        while(xc >= w):
            xc -= w
            yc += 1
        c.pos(xc, yc)

    def _print_prompt(self):
        c = self.console
        x, y = c.pos()
        
        n = c.write_scrolling(self.prompt, self.prompt_color)
        self.prompt_begin_pos = (x, y - n)
        self.prompt_end_pos = c.pos()
        self.size = c.size()

    def _update_prompt_pos(self, n):
        if n != 0:
            bx, by = self.prompt_begin_pos
            ex, ey = self.prompt_end_pos
            self.prompt_begin_pos = (bx, by - n)
            self.prompt_end_pos = (ex, ey - n)

    def _update_line(self):
        c=self.console
        c.cursor(0)         #Hide cursor avoiding flicking
        c.pos(*self.prompt_end_pos)
        ltext = self.l_buffer.quoted_text()
        if self.l_buffer.enable_selection and self.l_buffer.selection_mark>=0:
            start=len(self.l_buffer[:self.l_buffer.selection_mark].quoted_text())
            stop=len(self.l_buffer[:self.l_buffer.point].quoted_text())
            if start>stop:
                stop,start=start,stop
            n = c.write_scrolling(ltext[:start], self.command_color)
            n = c.write_scrolling(ltext[start:stop], self.selection_color)
            n = c.write_scrolling(ltext[stop:], self.command_color)
        else:
            n = c.write_scrolling(ltext, self.command_color)

        x,y = c.pos()       #Preserve one line for Asian IME(Input Method Editor) statusbar
        w,h = c.size()
        if y >= h - 1 or n > 0:
            c.scroll_window(-1)
            c.scroll((0,0,w,h),0,-1)
            n += 1

        self._update_prompt_pos(n)
        if hasattr(c,"clear_to_end_of_window"): #Work around function for ironpython due 
            c.clear_to_end_of_window()          #to System.Console's lack of FillFunction
        else:
            self._clear_after()
        c.cursor(1)         #Show cursor
        self._set_cursor()
    
    def readline(self, prompt=''):
        return self.mode.readline(prompt)

    def read_inputrc(self,inputrcpath=os.path.expanduser("~/pyreadlineconfig.ini")):
        modes=dict([(x.mode,x) for x in self.editingmodes])
        mode=self.editingmodes[0].mode
        def setmode(name):
            self.mode=modes[name]
        def bind_key(key,name):
            log("bind %s %s"%(key,name))
            if hasattr(modes[mode],name):
                modes[mode]._bind_key(key,getattr(modes[mode],name))
            else:
                print "Trying to bind unknown command '%s' to key '%s'"%(name,key)
        def un_bind_key(key):
            keyinfo = make_KeyPress_from_keydescr(key).tuple()
            if keyinfo in modes[mode].key_dispatch:
                del modes[mode].key_dispatch[keyinfo]

        def bind_exit_key(key):
            modes[mode]._bind_exit_key(key)
        def un_bind_exit_key(key):
            keyinfo = make_KeyPress_from_keydescr(key).tuple()
            if keyinfo in modes[mode].exit_dispatch:
                del modes[mode].exit_dispatch[keyinfo]

        def setkill_ring_to_clipboard(killring):
            import pyreadline.lineeditor.lineobj 
            pyreadline.lineeditor.lineobj.kill_ring_to_clipboard=killring
        def sethistoryfilename(filename):
            self._history.history_filename=os.path.expanduser(filename)
        def setbellstyle(mode):
            self.bell_style=mode
        def sethistorylength(length):
            self._history.history_length=int(length)
        def allow_ctrl_c(mode):
            log_sock("allow_ctrl_c:%s:%s"%(self.allow_ctrl_c,mode))
            self.allow_ctrl_c=mode
        def setbellstyle(mode):
            self.bell_style=mode
        def show_all_if_ambiguous(mode):
            self.show_all_if_ambiguous=mode
        def ctrl_c_tap_time_interval(mode):
            self.ctrl_c_tap_time_interval=mode
        def mark_directories(mode):
            self.mark_directories=mode
        def completer_delims(mode):
            self.completer_delims=mode
        def debug_output(on,filename="pyreadline_debug_log.txt"):  #Not implemented yet
            if on in ["on","on_nologfile"]:
                self.debug=True
            logger.start_log(on,filename)
            logger.log("STARTING LOG")
#            print release.branch
        def set_prompt_color(color):
            trtable={"black":0,"darkred":4,"darkgreen":2,"darkyellow":6,"darkblue":1,"darkmagenta":5,"darkcyan":3,"gray":7,
                     "red":4+8,"green":2+8,"yellow":6+8,"blue":1+8,"magenta":5+8,"cyan":3+8,"white":7+8}
            self.prompt_color=trtable.get(color.lower(),7)            
            
        def set_input_color(color):
            trtable={"black":0,"darkred":4,"darkgreen":2,"darkyellow":6,"darkblue":1,"darkmagenta":5,"darkcyan":3,"gray":7,
                     "red":4+8,"green":2+8,"yellow":6+8,"blue":1+8,"magenta":5+8,"cyan":3+8,"white":7+8}
            self.command_color=trtable.get(color.lower(),7)            
        loc={"branch":release.branch,
             "version":release.version,
             "mode":mode,
             "modes":modes,
             "set_mode":setmode,
             "bind_key":bind_key,
             "bind_exit_key":bind_exit_key,
             "un_bind_key":un_bind_key,
             "un_bind_exit_key":un_bind_exit_key,
             "bell_style":setbellstyle,
             "mark_directories":mark_directories,
             "show_all_if_ambiguous":show_all_if_ambiguous,
             "completer_delims":completer_delims,
             "debug_output":debug_output,
             "history_filename":sethistoryfilename,
             "history_length":sethistorylength,
             "set_prompt_color":set_prompt_color,
             "set_input_color":set_input_color,
             "allow_ctrl_c":allow_ctrl_c,
             "ctrl_c_tap_time_interval":ctrl_c_tap_time_interval,
             "kill_ring_to_clipboard":setkill_ring_to_clipboard,
             }
        if os.path.isfile(inputrcpath): 
            try:
                execfile(inputrcpath,loc,loc)
            except Exception,x:
                raise
                import traceback
                print >>sys.stderr, "Error reading .pyinputrc"
                filepath,lineno=traceback.extract_tb(sys.exc_traceback)[1][:2]
                print >>sys.stderr, "Line: %s in file %s"%(lineno,filepath)
                print >>sys.stderr, x
                raise ReadlineError("Error reading .pyinputrc")




def CTRL(c):
    '''make a control character'''
    assert '@' <= c <= '_'
    return chr(ord(c) - ord('@'))

# create a Readline object to contain the state
rl = Readline()


def GetOutputFile():
    '''Return the console object used by readline so that it can be used for printing in color.'''
    return rl.console

# make these available so this looks like the python readline module
parse_and_bind = rl.parse_and_bind
get_line_buffer = rl.get_line_buffer
insert_text = rl.insert_text
read_init_file = rl.read_init_file
add_history = rl.add_history
get_history_length = rl.get_history_length
set_history_length = rl.set_history_length
clear_history = rl.clear_history
read_history_file = rl.read_history_file
write_history_file = rl.write_history_file
set_completer = rl.set_completer
get_completer = rl.get_completer
get_begidx = rl.get_begidx
get_endidx = rl.get_endidx
set_completer_delims = rl.set_completer_delims
get_completer_delims = rl.get_completer_delims
set_startup_hook = rl.set_startup_hook
set_pre_input_hook = rl.set_pre_input_hook

if __name__ == '__main__':
    res = [ rl.readline('In[%d] ' % i) for i in range(3) ]
    print res
else:
    console.install_readline(rl.readline)
    pass
