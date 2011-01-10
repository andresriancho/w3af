#!/usr/bin/env python

import sys
sys.path.insert(1, "..")

from SOAPpy import *
server = SOAPProxy("http://206.135.217.234:8000/")
server.COM_SetProperty("Visible", 1)
server.Workbooks.Open("c:\\test.xls")
server.COM_NestedCall('ActiveSheet.Range("A2").EntireRow.Delete()')
server.quit()







