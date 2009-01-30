# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import re,operator,string,sys,os

#import wordmatcher
#import pyreadline.clipboard as clipboard
from pyreadline.unicode_helper import ensure_unicode,ensure_str
if "pyreadline" in sys.modules:
    pyreadline= sys.modules["pyreadline"]
else:
    import pyreadline

import lineobj

import exceptions

class EscapeHistory(exceptions.Exception):
    pass

from pyreadline.logger import log_sock

_ignore_leading_spaces=False

class LineHistory(object):
    def __init__(self):
        self.history=[]
        self._history_length=100
        self._history_cursor=0
        self.history_filename=os.path.expanduser('~/.history')
        self.lastcommand=None
        self.query=""

    def get_history_length(self):
        value=self._history_length
        log_sock("get_history_length:%d"%value,"history")
        return value

    def set_history_length(self,value):
        log_sock("set_history_length: old:%d new:%d"%(self._history_length,value),"history")
        self._history_length=value

    def get_history_cursor(self):
        value=self._history_cursor
        log_sock("get_history_cursor:%d"%value,"history")
        return value

    def set_history_cursor(self,value):
        log_sock("set_history_cursor: old:%d new:%d"%(self._history_cursor,value),"history")
        self._history_cursor=value
        
    history_length=property(get_history_length,set_history_length)
    history_cursor=property(get_history_cursor,set_history_cursor)

    def clear_history(self):
        '''Clear readline history.'''
        self.history[:] = []
        self.history_cursor = 0

    def read_history_file(self, filename=None): 
        '''Load a readline history file.'''
        if filename is None:
            filename=self.history_filename
        try:
            for line in open(filename, 'r'):
                self.add_history(lineobj.ReadLineTextBuffer(ensure_unicode(line.rstrip())))
        except IOError:
            self.history = []
            self.history_cursor = 0

    def write_history_file(self, filename=None): 
        '''Save a readline history file.'''
        if filename is None:
            filename=self.history_filename
        fp = open(filename, 'wb')
        for line in self.history[-self.history_length:]:
            fp.write(ensure_str(line.get_line_text()))
            fp.write('\n')
        fp.close()


    def add_history(self, line):
        '''Append a line to the history buffer, as if it was the last line typed.'''
        if not line.get_line_text():
            pass
        elif len(self.history) > 0 and self.history[-1].get_line_text() == line.get_line_text():
            pass
        else:
            self.history.append(line)
        self.history_cursor = len(self.history)

    def previous_history(self,current): # (C-p)
        '''Move back through the history list, fetching the previous command. '''
        if self.history_cursor==len(self.history):
            self.history.append(current.copy()) #do not use add_history since we do not want to increment cursor
            
        if self.history_cursor > 0:
            self.history_cursor -= 1
            current.set_line(self.history[self.history_cursor].get_line_text())
            current.point=lineobj.EndOfLine

    def next_history(self,current): # (C-n)
        '''Move forward through the history list, fetching the next command. '''
        if self.history_cursor < len(self.history)-1:
            self.history_cursor += 1
            current.set_line(self.history[self.history_cursor].get_line_text())

    def beginning_of_history(self): # (M-<)
        '''Move to the first line in the history.'''
        self.history_cursor = 0
        if len(self.history) > 0:
            self.l_buffer = self.history[0]

    def end_of_history(self,current): # (M->)
        '''Move to the end of the input history, i.e., the line currently
        being entered.'''
        self.history_cursor=len(self.history)
        current.set_line(self.history[-1].get_line_text())

    def reverse_search_history(self,searchfor,startpos=None):
        if startpos is None:
            startpos=self.history_cursor
        if _ignore_leading_spaces:
            res=[(idx,line.lstrip())  for idx,line in enumerate(self.history[startpos:0:-1]) if line.lstrip().startswith(searchfor.lstrip())]
        else:
            res=[(idx,line)  for idx,line in enumerate(self.history[startpos:0:-1]) if line.startswith(searchfor)]
        if res:
            self.history_cursor-=res[0][0]
            return res[0][1].get_line_text()
        return ""
        
    def forward_search_history(self,searchfor,startpos=None):
        if startpos is None:
            startpos=self.history_cursor
        if _ignore_leading_spaces:
            res=[(idx,line.lstrip()) for idx,line in enumerate(self.history[startpos:]) if line.lstrip().startswith(searchfor.lstrip())]
        else:
            res=[(idx,line) for idx,line in enumerate(self.history[startpos:]) if line.startswith(searchfor)]
        if res:
            self.history_cursor+=res[0][0]
            return res[0][1].get_line_text()
        return ""

    def _non_i_search(self, direction, current):
        c = pyreadline.rl.console
        line = current.get_line_text()
        query = ''
        while 1:
            c.pos(*pyreadline.rl.prompt_end_pos)
            scroll = c.write_scrolling(":%s" % query)
            pyreadline.rl._update_prompt_pos(scroll)
            pyreadline.rl._clear_after()

            event = c.getkeypress()
            
            if event.keyinfo.keyname == 'backspace':
                if len(query) > 0:
                    query = query[:-1]
                else:
                    break
            elif event.char in string.letters + string.digits + string.punctuation + ' ':
                query += event.char
            elif event.keyinfo.keyname == 'return':
                break
            else:
                pyreadline.rl._bell()
        res=""
        if query:
            if direction==-1:
                res=self.reverse_search_history(query)
                
            else:
                res=self.forward_search_history(query)
        return lineobj.ReadLineTextBuffer(res,point=0)
        
    def non_incremental_reverse_search_history(self,current): # (M-p)
        '''Search backward starting at the current line and moving up
        through the history as necessary using a non-incremental search for
        a string supplied by the user.'''
        return self._non_i_search(-1,current)

    def non_incremental_forward_search_history(self,current): # (M-n)
        '''Search forward starting at the current line and moving down
        through the the history as necessary using a non-incremental search
        for a string supplied by the user.'''
        return self._non_i_search(1,current)

    def _search(self, direction, partial):
        try:
            if (self.lastcommand != self.history_search_forward and
                    self.lastcommand != self.history_search_backward):
                self.query = ''.join(partial[0:partial.point].get_line_text())
            hcstart=max(self.history_cursor,0) 
            hc = self.history_cursor + direction
            while (direction < 0 and hc >= 0) or (direction > 0 and hc < len(self.history)):
                h = self.history[hc]
                if not self.query:
                    self.history_cursor = hc
                    result=lineobj.ReadLineTextBuffer(h,point=len(h.get_line_text()))
                    return result
                elif (h.get_line_text().startswith(self.query) and (h != partial.get_line_text())):
                    self.history_cursor = hc
                    result=lineobj.ReadLineTextBuffer(h,point=partial.point)
                    return result
                hc += direction
            else:
                if len(self.history)==0:
                    pass 
                elif hc>=len(self.history) and not self.query:
                    self.history_cursor=len(self.history)
                    return lineobj.ReadLineTextBuffer("",point=0)
                elif self.history[max(min(hcstart,len(self.history)-1),0)].get_line_text().startswith(self.query) and self.query:
                    return lineobj.ReadLineTextBuffer(self.history[max(min(hcstart,len(self.history)-1),0)],point=partial.point)
                else:                
                    return lineobj.ReadLineTextBuffer(partial,point=partial.point)
                return lineobj.ReadLineTextBuffer(self.query,point=min(len(self.query),partial.point))
        except IndexError:
            raise

    def history_search_forward(self,partial): # ()
        '''Search forward through the history for the string of characters
        between the start of the current line and the point. This is a
        non-incremental search. By default, this command is unbound.'''
        q= self._search(1,partial)
        return q

    def history_search_backward(self,partial): # ()
        '''Search backward through the history for the string of characters
        between the start of the current line and the point. This is a
        non-incremental search. By default, this command is unbound.'''
        
        q= self._search(-1,partial)
        return q

if __name__=="__main__":
    q=LineHistory()
    RL=lineobj.ReadLineTextBuffer
    q.add_history(RL("aaaa"))
    q.add_history(RL("aaba"))
    q.add_history(RL("aaca"))
    q.add_history(RL("akca"))
    q.add_history(RL("bbb"))
    q.add_history(RL("ako"))
