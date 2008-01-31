# -*- coding: latin-1 -*-
'''
session.py

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

import core.controllers.w3afCore as core
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.webUi.webMenu import webMenu
from core.controllers.threads.threadManager import threadManagerObj as tm

class session(webMenu):
    '''
    This is the session configuration menu for the web ui.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self ):
        webMenu.__init__(self)
        self._w3afCore = core.wCore

    def makeMenu(self):
        # Clear the document
        self._content.zero()
        self._content.addNL(2)
        self._content.write('''
        <div id="text">
        
        <p>Using this menu you can resume a previously saved session, please select the session file and click on "Resume".
        </p>
        
        </div>
        ''')
        
        # Write a form where the user can browse for the saved session
        # The form has a button that says "Resume"
        self._content.writeFormInit( self.getMenuName() , 'POST', self.getMenuName()+'.py')
        self._content.writeTextInput( 'resumeSession', 30, value='' )
        self._content.writeSubmit('Resume')
        self._content.writeFormEnd()
        self._content.addNL(2)
        
        self._content.write('<HR>')
        self._content.addNL(1)
        
        # Write a form where the user can set the NEW SESSION NAME
        # The form has a button that says "Save"
        self._content.write('''
        <div id="text">
        
        <p>You may also create a new session and continue with the configuration, to do so, choose a session filename and
        click on "Save".</p>
        
        </div>
        ''')
        self._content.writeFormInit( self.getMenuName() , 'POST', self.getMenuName()+'.py')
        self._content.writeTextInput( 'saveSession', 30, value='' )
        self._content.writeSubmit('Save')
        self._content.writeFormEnd()
        self._content.addNL(2)
        
        self.format()
        
        return self._content.read()
        
    def parsePOST(self, postData):
        '''
        This method is used to parse the POSTed options of the session configuration menu.
        It will configure session.
        '''
        # Clear the document
        self._content.zero()

        if 'resumeSession' in postData:
            sessionName = self.getName( postData['resumeSession'][0] )          
            
            try:
                tm.startFunction(self._w3afCore.resumeSession, ( sessionName, ), ownerObj=self )
            except w3afException, w3:
                self._content.writeError( str(w3) )
            else:
                self._content.writeMessage('<div id="text">Resumed session: '+sessionName+'</div>')
            
        elif 'saveSession' in postData:
            sessionName = self.getName( postData['saveSession'][0] )
            try:
                self._w3afCore.saveSession( sessionName )
            except Exception, e:
                self._content.writeError( str(e) )
            else:
                self._content.writeMessage('<div id="text">Session "'+sessionName+'" successfully created.</div>')
                self._content.writeNextBackPage('Plugins', 'plugins.py', 'URL Settings', 'urlSettings.py')
            
        else:
            self._content.writeError('Invalid call to session.py .')

        return self._content.read()

    def getName( self, largeName ):
        sessionName = '.'.join( largeName.split('.')[:-1] )
        return sessionName
