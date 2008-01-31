# -*- coding: latin-1 -*-
'''
start.py

Copyright 2007 Mariano Nuñez Di Croce @ CYBSEC

This file is part of w3af, http://www.cybsec.com/EN/research/tools/w3af.php

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
# Import w3af
import core.controllers.w3afCore as core
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.webUi.webMenu import webMenu
from core.controllers.threads.threadManager import threadManagerObj as tm

class start(webMenu):
    '''
    This is the start menu for the Web Interface
    
    @author: Mariano Nuñez Di Croce <mnunez@cybsec.com>
    '''
    def __init__( self ):
        webMenu.__init__(self)
        self._w3af = core.wCore
        self._intCache = ''
        self._refreshTime = 3000
        self._started = False

    def makeMenu(self):
        '''
        This must start w3af plugins.
        This method is called many times, once for every window refresh
        '''
        # Clear the document
        self._content.zero()

        if not self._started:
            try:
                tm.startFunction(self._w3af.start, (), restrict=False, ownerObj=self )
            except w3afException, e:
                self._content.writeError( str(e) )
            except AssertionError, ae:
                self._content.writeError( str(ae) )
            else:
                self._content.write( '<script>openStartWindow();</script>'  )
                self._started = True
        
        else:
            # Refresh js function
            res = ''.join([str(f) for f in om.out.getMessageCache()])
            res = res.replace('\n','<br>')
            self._intCache += res
            self._content.write( self._intCache )
        
        return self._content.read()
    
