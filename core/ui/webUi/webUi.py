# -*- coding: latin-1 -*-
'''
webMenu.py

Copyright 2007 Mariano Nuñez Di Croce @ CYBSEC

This file is part of sapyto, http://www.cybsec.com/EN/research/tools/sapyto.php

sapyto is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

sapyto is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with sapyto; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
import core.ui.webUi.plugins as plugins
import core.ui.webUi.webserver as ws
# for parsing options
import xml.dom.minidom
import os
import core.data.constants.w3afPorts as w3afPorts

class webUi:
    '''
    This class is the Web Interface.
    
    @author: Mariano Nuñez Di Croce <mnunez@cybsec.com>
    '''
    def __init__( self ):
        self._ip = '127.0.0.1'
        self._port = w3afPorts.WEBUI
        self._webroot = 'core'+ os.path.sep +'ui' + os.path.sep + 'webUi'+ os.path.sep + 'webroot'
        
    def sh(self):
        om.out.error('The web user interface has been deprecated, if you want a graphical user interface please use the gtkUi  ( ./w3af -g ).')
        #om.out.console('Starting w3af Web Interface at: http://localhost:'+str(self._port)+'/')
        #webServer = ws.webserver(self._ip, self._port, self._webroot)
        #webServer.run()
        #webServer.start2()
    
    
