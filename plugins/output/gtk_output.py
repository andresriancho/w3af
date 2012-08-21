'''
gtk_output.py

Copyright 2008 Andres Riancho

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
import time
import Queue

import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity

from core.controllers.plugins.output_plugin import OutputPlugin


class gtk_output(OutputPlugin):
    '''
    Saves messages to kb.kb.getData('gtk_output', 'queue') to be displayed in the UI.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        OutputPlugin.__init__(self)
        if not kb.kb.getData('gtk_output', 'queue') == []:
            self.queue = kb.kb.getData('gtk_output', 'queue')
        else:
            self.queue = Queue.Queue(500)
            kb.kb.save('gtk_output', 'queue' , self.queue)

    def debug(self, msg_string, newLine=True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for debug messages.
        '''
        #
        #   I don't really want to add debug messages to the queue, as they are only used
        #   in the time graph that's displayed under the log. In order to save some memory
        #   I'm only creating the object, but without any msg.
        #
        m = message( 'debug', '', newLine )
        self._addToQueue( m )
    
    def information(self, msg_string , newLine=True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for informational messages.
        ''' 
        m = message( 'information', self._clean_string(msg_string), newLine )
        self._addToQueue( m )

    def error(self, msg_string , newLine=True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for error messages.
        '''     
        m = message( 'error', self._clean_string(msg_string), newLine )
        self._addToQueue( m )

    def vulnerability(self, msg_string , newLine=True, severity=severity.MEDIUM ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action when a vulnerability is found.
        '''     
        m = message( 'vulnerability', self._clean_string(msg_string), newLine )
        m.setSeverity( severity )
        self._addToQueue( m )
        
    def console( self, msg_string, newLine=True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        m = message( 'console', self._clean_string(msg_string), newLine )
        self._addToQueue( m )
    
    def _addToQueue( self, m ):
        '''
        Adds a message object to the queue. If the queue isn't there, it creates one.
        '''
        self.queue.put( m )
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Saves messages to kb.kb.getData('gtk_output', 'queue'), messages are
        saved in the form of objects. This plugin was created to be able to
        communicate with the gtkUi and should be enabled if you are using it.
        '''


class message:
    def __init__( self, msg_type, msg, newLine=True ):
        '''
        @parameter msg_type: console, information, vulnerability, etc
        @parameter msg: The message itself
        @parameter newLine: Should I print a newline ? True/False
        '''
        self._type = msg_type
        self._msg = msg
        self._newLine = newLine
        self._time = time.time()
        self._severity = None
    
    def getSeverity( self ):
        return self._severity
        
    def setSeverity( self, the_severity ):
        self._severity = the_severity
    
    def getMsg( self ):
        return self._msg
    
    def getType( self ):
        return self._type
        
    def getNewLine( self ):
        return self._newLine
        
    def getRealTime( self ):
        return self._time

    def getTime( self ):
        return time.strftime("%c", time.localtime(self._time))
