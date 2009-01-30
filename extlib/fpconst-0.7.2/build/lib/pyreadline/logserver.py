# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import socket


try:
    import msvcrt
except ImportError:
    msvcrt=None
    print "problem"
        


port =8081

s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

s.bind(("",port))
s.settimeout(0.05)

print "Starting logserver on port:",port
print "Press q to quit logserver",port
singleline=False


def check_key():
    if msvcrt is None:
        return False
    else:
        if msvcrt.kbhit()!=0:
            q=msvcrt.getch()
            
            return q in "q" 
        else:
            return False


while 1:
    try:
        data,addr=s.recvfrom(1024)
    except socket.timeout:
        if check_key():
            print "Quitting logserver"
            break
        else:
            continue
    if data.startswith("@@"):
        continue
    if singleline:
        print "\r"," "*78,"\r",data,#,addr
    else:
        print data
    
    

