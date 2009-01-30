# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Jörgen Stenarson. <>

import sys, unittest
sys.path.append ('../..')
#from pyreadline.modes.vi import *
#from pyreadline import keysyms
from pyreadline.lineeditor import lineobj
from pyreadline.lineeditor.history import LineHistory
import pyreadline.lineeditor.history as history

import pyreadline.logger
pyreadline.logger.sock_silent=False
from pyreadline.logger import log_sock
#----------------------------------------------------------------------


#----------------------------------------------------------------------
RL=lineobj.ReadLineTextBuffer

class Test_linepos (unittest.TestCase):
    t="test text"

    def init_test(self):
        history._ignore_leading_spaces=False
        self.q=q=LineHistory()
        for x in ["aaaa","aaba","aaca","akca","bbb","ako"]:
            q.add_history(RL(x))

    def test_previous_history (self):
        self.init_test()
        hist=self.q
        assert hist.history_cursor==6
        l=RL("")
        hist.previous_history(l)
        assert l.get_line_text()=="ako"
        hist.previous_history(l)
        assert l.get_line_text()=="bbb"
        hist.previous_history(l)
        assert l.get_line_text()=="akca"
        hist.previous_history(l)
        assert l.get_line_text()=="aaca"
        hist.previous_history(l)
        assert l.get_line_text()=="aaba"
        hist.previous_history(l)
        assert l.get_line_text()=="aaaa"
        hist.previous_history(l)
        assert l.get_line_text()=="aaaa"

    def test_next_history (self):
        self.init_test()
        hist=self.q
        hist.beginning_of_history()
        assert hist.history_cursor==0
        l=RL("")
        hist.next_history(l)
        assert l.get_line_text()=="aaba"
        hist.next_history(l)
        assert l.get_line_text()=="aaca"
        hist.next_history(l)
        assert l.get_line_text()=="akca"
        hist.next_history(l)
        assert l.get_line_text()=="bbb"
        hist.next_history(l)
        assert l.get_line_text()=="ako"
        hist.next_history(l)
        assert l.get_line_text()=="ako"

    def init_test2(self):
        self.q=q=LineHistory()
        for x in ["aaaa","aaba","aaca","akca","bbb","ako"]:
            q.add_history(RL(x))
        
    def test_history_search_backward (self):
        history._ignore_leading_spaces=False
        q=LineHistory()
        for x in ["aaaa","aaba","aaca","    aacax","akca","bbb","ako"]:
            q.add_history(RL(x))
        a=RL("aa",point=2)
        for x in ["aaca","aaba","aaaa","aaaa"]:
            res=q.history_search_backward(a)
            assert res.get_line_text()==x
        
    def test_history_search_forward (self):
        history._ignore_leading_spaces=False
        q=LineHistory()
        for x in ["aaaa","aaba","aaca","    aacax","akca","bbb","ako"]:
            q.add_history(RL(x))
        q.beginning_of_history()
        a=RL("aa",point=2)
        for x in ["aaba","aaca","aaca"]:
            res=q.history_search_forward(a)
            assert res.get_line_text()==x


#----------------------------------------------------------------------
# utility functions

#----------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()

    l=lineobj.ReadLineTextBuffer("First Second Third")