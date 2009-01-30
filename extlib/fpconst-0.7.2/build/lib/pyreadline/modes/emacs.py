# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2003-2006 Gary Bishop.
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import os,sys,time
import pyreadline.logger as logger
from   pyreadline.logger import log,log_sock
from pyreadline.lineeditor.lineobj import Point
import pyreadline.lineeditor.lineobj as lineobj
import pyreadline.lineeditor.history as history
import basemode
import string
from pyreadline.unicode_helper import ensure_unicode

def format(keyinfo):
    if len(keyinfo[-1])!=1:
        k=keyinfo+(-1,)
    else:
        k=keyinfo+(ord(keyinfo[-1]),)
    
    return "(%s,%s,%s,%s,%x)"%k
in_ironpython="IronPython" in sys.version


class EmacsMode(basemode.BaseMode):
    mode="emacs"
    def __init__(self,rlobj):
        super(EmacsMode,self).__init__(rlobj)
        self._keylog=(lambda x,y: None)
        self.previous_func=None
        self.prompt=">>>"
    def __repr__(self):
        return "<EmacsMode>"

    def add_key_logger(self,logfun):
        """logfun should be function that takes disp_fun and line_buffer object """
        self._keylog=logfun
        
    def _readline_from_keyboard(self):
        c=self.console
        def nop(e):
            pass
        while 1:
            self._update_line()
            lbuf=self.l_buffer
            log_sock("point:%d mark:%d selection_mark:%d"%(lbuf.point,lbuf.mark,lbuf.selection_mark))
            try:
                event = c.getkeypress()
                log_sock(u">>%s"%event)
            except KeyboardInterrupt:
                from pyreadline.keysyms.common import KeyPress
                from pyreadline.console.event import Event
                event=Event(0,0)
                event.char="c"
                event.keyinfo=KeyPress("c",shift=False,control=True,meta=False,keyname=None)
                log_sock("KBDIRQ")
                if self.allow_ctrl_c:
                    now=time.time()
                    if (now-self.ctrl_c_timeout)<self.ctrl_c_tap_time_interval:
                        raise
                    else:
                        self.ctrl_c_timeout=now
                    pass
                else:
                    raise
            if self.next_meta:
                self.next_meta = False
                control, meta, shift, code = event.keyinfo
                event.keyinfo = (control, True, shift, code)

            #Process exit keys. Only exit on empty line
            keyinfo=event.keyinfo.tuple()
            if keyinfo in self.exit_dispatch:
                if lineobj.EndOfLine(self.l_buffer) == 0:
                    raise EOFError
            if len(keyinfo[-1])>1:
                default=nop
            else:
                default=self.self_insert
            dispatch_func = self.key_dispatch.get(keyinfo,default)
            
            log("readline from keyboard:%s,%s"%(keyinfo,dispatch_func))
            log_sock((u"%s|%s"%(ensure_unicode(format(keyinfo)),dispatch_func.__name__)),"bound_function")
            r = None
            if dispatch_func:
                r = dispatch_func(event)
                self._keylog(dispatch_func,self.l_buffer)
                self.l_buffer.push_undo()

            self.previous_func = dispatch_func
            if r:
                self._update_line()
                break

    def readline(self, prompt=''):
        '''Try to act like GNU readline.'''
        # handle startup_hook
        self.ctrl_c_timeout=time.time()
        self.l_buffer.selection_mark=-1
        if self.first_prompt:
            self.first_prompt = False
            if self.startup_hook:
                try:
                    self.startup_hook()
                except:
                    print 'startup hook failed'
                    traceback.print_exc()

        c = self.console
        self.l_buffer.reset_line()
        self.prompt = prompt
        self._print_prompt()

        if self.pre_input_hook:
            try:
                self.pre_input_hook()
            except:
                print 'pre_input_hook failed'
                traceback.print_exc()
                self.pre_input_hook = None

        log("in readline: %s"%self.paste_line_buffer)
        if len(self.paste_line_buffer)>0:
            self.l_buffer=lineobj.ReadLineTextBuffer(self.paste_line_buffer[0])
            self._update_line()
            self.paste_line_buffer=self.paste_line_buffer[1:]
            c.write('\r\n')
        else:
            self._readline_from_keyboard()
            c.write('\r\n')

        self.add_history(self.l_buffer.copy())

        log('returning(%s)' % self.l_buffer.get_line_text())
        return self.l_buffer.get_line_text() + '\n'

#########  History commands
    def previous_history(self, e): # (C-p)
        '''Move back through the history list, fetching the previous command. '''
        self._history.previous_history(self.l_buffer)
        self.l_buffer.point=lineobj.EndOfLine
        
    def next_history(self, e): # (C-n)
        '''Move forward through the history list, fetching the next command. '''
        self._history.next_history(self.l_buffer)

    def beginning_of_history(self, e): # (M-<)
        '''Move to the first line in the history.'''
        self._history.beginning_of_history()

    def end_of_history(self, e): # (M->)
        '''Move to the end of the input history, i.e., the line currently
        being entered.'''
        self._history.end_of_history(self.l_buffer)

    def _i_search(self, searchfun, direction, init_event):
        c = self.console
        line = self.l_buffer.get_line_text()
        query = ''
        if (self.previous_func != self.history_search_forward and
                self.previous_func != self.history_search_backward):
            self.query = ''.join(self.l_buffer[0:Point].get_line_text())
        hc_start = self._history.history_cursor #+ direction
        while 1:
            x, y = self.prompt_end_pos
            c.pos(0, y)
            if direction < 0:
                prompt = 'reverse-i-search'
            else:
                prompt = 'forward-i-search'

            scroll = c.write_scrolling("%s`%s': %s" % (prompt, query, line))
            self._update_prompt_pos(scroll)
            self._clear_after()

            event = c.getkeypress()
            if event.keyinfo.keyname == 'backspace':
                query = query[:-1]
                if len(query) > 0:
                    #self._history.history_cursor = hc_start  #forces search to restart when search empty
                    line=searchfun(query)                
                else:
                    self._bell()
                    line=""   #empty query means no search result
            elif event.char in string.letters + string.digits + string.punctuation + ' ':
                #self._history.history_cursor = hc_start
                query += event.char
                line=searchfun(query)
            elif event.keyinfo == init_event.keyinfo:
                self._history.history_cursor += direction
                line=searchfun(query)                
            else:
                if event.keyinfo.keyname != 'return':
                    self._bell()
                break

        px, py = self.prompt_begin_pos
        c.pos(0, py)
        self.l_buffer.set_line(line)
        self._print_prompt()
        self._history.history_cursor=len(self._history.history)

    def reverse_search_history(self, e): # (C-r)
        '''Search backward starting at the current line and moving up
        through the history as necessary. This is an incremental search.'''
        self._i_search(self._history.reverse_search_history, -1, e)

    def forward_search_history(self, e): # (C-s)
        '''Search forward starting at the current line and moving down
        through the the history as necessary. This is an incremental search.'''
        self._i_search(self._history.forward_search_history, 1, e)


    def non_incremental_reverse_search_history(self, e): # (M-p)
        '''Search backward starting at the current line and moving up
        through the history as necessary using a non-incremental search for
        a string supplied by the user.'''
        q=self._history.non_incremental_reverse_search_history(self.l_buffer)
        self.l_buffer=q

    def non_incremental_forward_search_history(self, e): # (M-n)
        '''Search forward starting at the current line and moving down
        through the the history as necessary using a non-incremental search
        for a string supplied by the user.'''
        q=self._history.non_incremental_reverse_search_history(self.l_buffer)
        self.l_buffer=q

    def history_search_forward(self, e): # ()
        '''Search forward through the history for the string of characters
        between the start of the current line and the point. This is a
        non-incremental search. By default, this command is unbound.'''
        if self.previous_func and hasattr(self._history,self.previous_func.__name__):
            self._history.lastcommand=getattr(self._history,self.previous_func.__name__)
        else:
            self._history.lastcommand=None
        q=self._history.history_search_forward(self.l_buffer)
        self.l_buffer=q
        self.l_buffer.point=q.point

    def history_search_backward(self, e): # ()
        '''Search backward through the history for the string of characters
        between the start of the current line and the point. This is a
        non-incremental search. By default, this command is unbound.'''
        if self.previous_func and hasattr(self._history,self.previous_func.__name__):
            self._history.lastcommand=getattr(self._history,self.previous_func.__name__)
        else:
            self._history.lastcommand=None
        q=self._history.history_search_backward(self.l_buffer)
        self.l_buffer=q
        self.l_buffer.point=q.point


    def yank_nth_arg(self, e): # (M-C-y)
        '''Insert the first argument to the previous command (usually the
        second word on the previous line) at point. With an argument n,
        insert the nth word from the previous command (the words in the
        previous command begin with word 0). A negative argument inserts the
        nth word from the end of the previous command.'''
        pass

    def yank_last_arg(self, e): # (M-. or M-_)
        '''Insert last argument to the previous command (the last word of
        the previous history entry). With an argument, behave exactly like
        yank-nth-arg. Successive calls to yank-last-arg move back through
        the history list, inserting the last argument of each line in turn.'''
        pass

    def forward_backward_delete_char(self, e): # ()
        '''Delete the character under the cursor, unless the cursor is at
        the end of the line, in which case the character behind the cursor
        is deleted. By default, this is not bound to a key.'''
        pass

    def quoted_insert(self, e): # (C-q or C-v)
        '''Add the next character typed to the line verbatim. This is how to
        insert key sequences like C-q, for example.'''
        e = self.console.getkeypress()
        self.insert_text(e.char)

    def tab_insert(self, e): # (M-TAB)
        '''Insert a tab character. '''
        ws = ' ' * (self.tabstop - (self.line_cursor%self.tabstop))
        self.insert_text(ws)

    def transpose_chars(self, e): # (C-t)
        '''Drag the character before the cursor forward over the character
        at the cursor, moving the cursor forward as well. If the insertion
        point is at the end of the line, then this transposes the last two
        characters of the line. Negative arguments have no effect.'''
        self.l_buffer.transpose_chars()

    def transpose_words(self, e): # (M-t)
        '''Drag the word before point past the word after point, moving
        point past that word as well. If the insertion point is at the end
        of the line, this transposes the last two words on the line.'''
        self.l_buffer.transpose_words()

    def overwrite_mode(self, e): # ()
        '''Toggle overwrite mode. With an explicit positive numeric
        argument, switches to overwrite mode. With an explicit non-positive
        numeric argument, switches to insert mode. This command affects only
        emacs mode; vi mode does overwrite differently. Each call to
        readline() starts in insert mode. In overwrite mode, characters
        bound to self-insert replace the text at point rather than pushing
        the text to the right. Characters bound to backward-delete-char
        replace the character before point with a space.'''
        pass
        
    def kill_line(self, e): # (C-k)
        '''Kill the text from point to the end of the line. '''
        self.l_buffer.kill_line()
        
    def backward_kill_line(self, e): # (C-x Rubout)
        '''Kill backward to the beginning of the line. '''
        self.l_buffer.backward_kill_line()

    def unix_line_discard(self, e): # (C-u)
        '''Kill backward from the cursor to the beginning of the current line. '''
        # how is this different from backward_kill_line?
        self.l_buffer.unix_line_discard()

    def kill_whole_line(self, e): # ()
        '''Kill all characters on the current line, no matter where point
        is. By default, this is unbound.'''
        self.l_buffer.kill_whole_line()

    def kill_word(self, e): # (M-d)
        '''Kill from point to the end of the current word, or if between
        words, to the end of the next word. Word boundaries are the same as
        forward-word.'''
        self.l_buffer.kill_word()
    forward_kill_word=kill_word
    
    def backward_kill_word(self, e): # (M-DEL)
        '''Kill the word behind point. Word boundaries are the same as
        backward-word. '''
        self.l_buffer.backward_kill_word()

    def unix_word_rubout(self, e): # (C-w)
        '''Kill the word behind point, using white space as a word
        boundary. The killed text is saved on the kill-ring.'''
        self.l_buffer.unix_word_rubout()

    def kill_region(self, e): # ()
        '''Kill the text in the current region. By default, this command is unbound. '''
        pass

    def copy_region_as_kill(self, e): # ()
        '''Copy the text in the region to the kill buffer, so it can be
        yanked right away. By default, this command is unbound.'''
        pass

    def copy_backward_word(self, e): # ()
        '''Copy the word before point to the kill buffer. The word
        boundaries are the same as backward-word. By default, this command
        is unbound.'''
        pass

    def copy_forward_word(self, e): # ()
        '''Copy the word following point to the kill buffer. The word
        boundaries are the same as forward-word. By default, this command is
        unbound.'''
        pass


    def yank(self, e): # (C-y)
        '''Yank the top of the kill ring into the buffer at point. '''
        self.l_buffer.yank()

    def yank_pop(self, e): # (M-y)
        '''Rotate the kill-ring, and yank the new top. You can only do this
        if the prior command is yank or yank-pop.'''
        self.l_buffer.yank_pop()


    def digit_argument(self, e): # (M-0, M-1, ... M--)
        '''Add this digit to the argument already accumulating, or start a
        new argument. M-- starts a negative argument.'''
        args=e.char

        c = self.console
        line = self.l_buffer.get_line_text()
        oldprompt=self.prompt
        def nop(e):
            pass
        while 1:
            x, y = self.prompt_end_pos
            c.pos(0, y)
            self.prompt="(arg: %s) "%args
            self._print_prompt()
            self._update_line()

            event = c.getkeypress()
            if event.keyinfo.keyname == 'enter':
                break
            elif event.char in "0123456789":
                args+=event.char
            else:
                self.argument=int(args)
                keyinfo=event.keyinfo.tuple()
                if len(keyinfo[-1])>1:
                    default=nop
                else:
                    default=self.self_insert
                dispatch_func = self.key_dispatch.get(keyinfo,default)
                dispatch_func(event)
                break
        self.prompt=oldprompt
        x, y = self.prompt_end_pos
        c.pos(0, y)
        self._print_prompt()
        self._update_line()

            


    def universal_argument(self, e): # ()
        '''This is another way to specify an argument. If this command is
        followed by one or more digits, optionally with a leading minus
        sign, those digits define the argument. If the command is followed
        by digits, executing universal-argument again ends the numeric
        argument, but is otherwise ignored. As a special case, if this
        command is immediately followed by a character that is neither a
        digit or minus sign, the argument count for the next command is
        multiplied by four. The argument count is initially one, so
        executing this function the first time makes the argument count
        four, a second time makes the argument count sixteen, and so on. By
        default, this is not bound to a key.'''
        pass

    def delete_char_or_list(self, e): # ()
        '''Deletes the character under the cursor if not at the beginning or
        end of the line (like delete-char). If at the end of the line,
        behaves identically to possible-completions. This command is unbound
        by default.'''
        pass

    def start_kbd_macro(self, e): # (C-x ()
        '''Begin saving the characters typed into the current keyboard macro. '''
        pass

    def end_kbd_macro(self, e): # (C-x ))
        '''Stop saving the characters typed into the current keyboard macro
        and save the definition.'''
        pass

    def call_last_kbd_macro(self, e): # (C-x e)
        '''Re-execute the last keyboard macro defined, by making the
        characters in the macro appear as if typed at the keyboard.'''
        pass

    def re_read_init_file(self, e): # (C-x C-r)
        '''Read in the contents of the inputrc file, and incorporate any
        bindings or variable assignments found there.'''
        pass

    def abort(self, e): # (C-g)
        '''Abort the current editing command and ring the terminals bell
             (subject to the setting of bell-style).'''
        self._bell()

    def do_uppercase_version(self, e): # (M-a, M-b, M-x, ...)
        '''If the metafied character x is lowercase, run the command that is
        bound to the corresponding uppercase character.'''
        pass

    def prefix_meta(self, e): # (ESC)
        '''Metafy the next character typed. This is for keyboards without a
        meta key. Typing ESC f is equivalent to typing M-f. '''
        self.next_meta = True

    def undo(self, e): # (C-_ or C-x C-u)
        '''Incremental undo, separately remembered for each line.'''
        self.l_buffer.pop_undo()

    def revert_line(self, e): # (M-r)
        '''Undo all changes made to this line. This is like executing the
        undo command enough times to get back to the beginning.'''
        pass

    def tilde_expand(self, e): # (M-~)
        '''Perform tilde expansion on the current word.'''
        pass

    def set_mark(self, e): # (C-@)
        '''Set the mark to the point. If a numeric argument is supplied, the
        mark is set to that position.'''
        self.l_buffer.set_mark()

    def exchange_point_and_mark(self, e): # (C-x C-x)
        '''Swap the point with the mark. The current cursor position is set
        to the saved position, and the old cursor position is saved as the
        mark.'''
        pass

    def character_search(self, e): # (C-])
        '''A character is read and point is moved to the next occurrence of
        that character. A negative count searches for previous occurrences.'''
        pass

    def character_search_backward(self, e): # (M-C-])
        '''A character is read and point is moved to the previous occurrence
        of that character. A negative count searches for subsequent
        occurrences.'''
        pass

    def insert_comment(self, e): # (M-#)
        '''Without a numeric argument, the value of the comment-begin
        variable is inserted at the beginning of the current line. If a
        numeric argument is supplied, this command acts as a toggle: if the
        characters at the beginning of the line do not match the value of
        comment-begin, the value is inserted, otherwise the characters in
        comment-begin are deleted from the beginning of the line. In either
        case, the line is accepted as if a newline had been typed.'''
        pass

    def dump_variables(self, e): # ()
        '''Print all of the settable variables and their values to the
        Readline output stream. If a numeric argument is supplied, the
        output is formatted in such a way that it can be made part of an
        inputrc file. This command is unbound by default.'''
        pass

    def dump_macros(self, e): # ()
        '''Print all of the Readline key sequences bound to macros and the
        strings they output. If a numeric argument is supplied, the output
        is formatted in such a way that it can be made part of an inputrc
        file. This command is unbound by default.'''
        pass


    #Create key bindings:

    def init_editing_mode(self, e): # (C-e)
        '''When in vi command mode, this causes a switch to emacs editing
        mode.'''
        self._bind_exit_key('Control-d')
        self._bind_exit_key('Control-z')

        # I often accidentally hold the shift or control while typing space
        self._bind_key('space',       self.self_insert)
        self._bind_key('Shift-space',       self.self_insert)
        self._bind_key('Control-space',     self.self_insert)
        self._bind_key('Return',            self.accept_line)
        self._bind_key('Left',              self.backward_char)
        self._bind_key('Control-b',         self.backward_char)
        self._bind_key('Right',             self.forward_char)
        self._bind_key('Control-f',         self.forward_char)
        self._bind_key('BackSpace',         self.backward_delete_char)
        self._bind_key('Control-BackSpace', self.backward_delete_word)
        
        self._bind_key('Home',              self.beginning_of_line)
        self._bind_key('End',               self.end_of_line)
        self._bind_key('Delete',            self.delete_char)
        self._bind_key('Control-d',         self.delete_char)
        self._bind_key('Clear',             self.clear_screen)
        self._bind_key('Alt-f',             self.forward_word)
        self._bind_key('Alt-b',             self.backward_word)
        self._bind_key('Control-l',         self.clear_screen)
        self._bind_key('Control-p',         self.previous_history)
        self._bind_key('Up',                self.history_search_backward)
        self._bind_key('Control-n',         self.next_history)
        self._bind_key('Down',              self.history_search_forward)
        self._bind_key('Control-a',         self.beginning_of_line)
        self._bind_key('Control-e',         self.end_of_line)
        self._bind_key('Alt-<',             self.beginning_of_history)
        self._bind_key('Alt->',             self.end_of_history)
        self._bind_key('Control-r',         self.reverse_search_history)
        self._bind_key('Control-s',         self.forward_search_history)
        self._bind_key('Alt-p',             self.non_incremental_reverse_search_history)
        self._bind_key('Alt-n',             self.non_incremental_forward_search_history)
        self._bind_key('Control-z',         self.undo)
        self._bind_key('Control-_',         self.undo)
        self._bind_key('Escape',            self.kill_whole_line)
        self._bind_key('Meta-d',            self.kill_word)
        self._bind_key('Control-Delete',       self.forward_delete_word)
        self._bind_key('Control-w',         self.unix_word_rubout)
        #self._bind_key('Control-Shift-v',   self.quoted_insert)
        self._bind_key('Control-v',         self.paste)
        self._bind_key('Alt-v',             self.ipython_paste)
        self._bind_key('Control-y',         self.yank)
        self._bind_key('Control-k',         self.kill_line)
        self._bind_key('Control-m',         self.set_mark)
        self._bind_key('Control-q',         self.copy_region_to_clipboard)
#        self._bind_key('Control-shift-k',  self.kill_whole_line)
        self._bind_key('Control-Shift-v',   self.paste_mulitline_code)
        self._bind_key("Control-Right",     self.forward_word_end)
        self._bind_key("Control-Left",      self.backward_word)
        self._bind_key("Shift-Right",       self.forward_char_extend_selection)
        self._bind_key("Shift-Left",        self.backward_char_extend_selection)
        self._bind_key("Shift-Control-Right",     self.forward_word_end_extend_selection)
        self._bind_key("Shift-Control-Left",     self.backward_word_extend_selection)
        self._bind_key("Shift-Home",        self.beginning_of_line_extend_selection)
        self._bind_key("Shift-End",         self.end_of_line_extend_selection)
        self._bind_key("numpad0",           self.self_insert)
        self._bind_key("numpad1",           self.self_insert)
        self._bind_key("numpad2",           self.self_insert)
        self._bind_key("numpad3",           self.self_insert)
        self._bind_key("numpad4",           self.self_insert)
        self._bind_key("numpad5",           self.self_insert)
        self._bind_key("numpad6",           self.self_insert)
        self._bind_key("numpad7",           self.self_insert)
        self._bind_key("numpad8",           self.self_insert)
        self._bind_key("numpad9",           self.self_insert)
        self._bind_key("add",               self.self_insert)
        self._bind_key("subtract",          self.self_insert)
        self._bind_key("multiply",          self.self_insert)
        self._bind_key("divide",            self.self_insert)
        self._bind_key("vk_decimal",        self.self_insert)
        log("RUNNING INIT EMACS")

# make it case insensitive
def commonprefix(m):
    "Given a list of pathnames, returns the longest common leading component"
    if not m: return ''
    prefix = m[0]
    for item in m:
        for i in range(len(prefix)):
            if prefix[:i+1].lower() != item[:i+1].lower():
                prefix = prefix[:i]
                if i == 0: return ''
                break
    return prefix

