# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import socket
from pyreadline.unicode_helper import ensure_str
_logfile=False

def start_log(on,filename):
    global _logfile
    if on=="on":
        _logfile=open(filename,"w")
    else:
        _logfile=False
        
def log(s):
    if _logfile:
        s = ensure_str(s)
        print >>_logfile, s
        _logfile.flush()


host="localhost"
port=8081
logsocket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

show_event=["keypress","bound_function","bind_key","console"]
show_event=["bound_function"]

sock_silent=True

def log_sock(s,event_type=None):
    if sock_silent:
        pass
    else:
        if event_type is None:
            logsocket.sendto(ensure_str(s),(host,port))
        elif event_type in show_event:
            logsocket.sendto(ensure_str(s),(host,port))
        else:
            pass

    
