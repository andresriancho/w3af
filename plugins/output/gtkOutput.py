'''
gtkOutput.py

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


from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import *

# The output plugin must know the session name that is saved in the config object,
# the session name is assigned in the target settings
import core.data.kb.config as cf

import Queue

# The database handler class
from extlib.buzhug.buzhug import Base

from core.controllers.misc.homeDir import getHomeDir

# Only to be used with care.
import core.controllers.outputManager as om
import os

# I'm timestamping the messages
import time

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

# severity constants
import core.data.constants.severity as severity

class gtkOutput(baseOutputPlugin):
    '''
    Saves messages to kb.kb.getData('gtkOutput', 'queue'), messages are saved in the form of objects.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self.queue = Queue.Queue()
        kb.kb.save( 'gtkOutput', 'queue' , self.queue )
        baseOutputPlugin.__init__(self)
        
        sessionName = cf.cf.getData('sessionName')
        db_req_res_dirName = os.path.join(getHomeDir(), 'sessions', 'db_req_' + sessionName )
        
        try:
            os.mkdir(os.path.join(getHomeDir() , 'sessions'))
        except OSError, oe:
            # [Errno 17] File exists
            if oe.errno != 17:
                raise w3afException('Unable to write to the user home directory: ' + getHomeDir() )
            
        try:
            self._del_dir(db_req_res_dirName)
        except Exception, e:
            # I get here when the session directory for this db wasn't created
            # and when the user has no permissions to remove the directory
            # FIXME: handle those errors!
            pass

        if kb.kb.getData('gtkOutput', 'db') == []:
            # Create the DB object
            try:
                self._db_req_res = Base( db_req_res_dirName )
            except Exception, e:
                raise w3afException('An exception was raised while creating the gtkOutput database object: ' + str(e) )
            else:
                try:
                    # Create the database
                    self._db_req_res.create( ('id',int), ('method', str), ('uri', str), ('http_version', str), ('request_headers', str), ('postdata', str), 
                                                        ('code', int), ('msg', str), ('response_headers', str), ('body', str), ('time',float) )
                except IOError, ioe:
                    # hmmm , the database already existed...
                    raise w3afException('An exception was raised while creating the gtkOutput database files: ' + str(e) )
                else:
                    kb.kb.save('gtkOutput', 'db', self._db_req_res )
        else:
            # Restore it from the kb
            self._db_req_res = kb.kb.getData('gtkOutput', 'db')
    
    def _del_dir(self,path):
        for file in os.listdir(path):
            file_or_dir = os.path.join(path,file)
            if os.path.isdir(file_or_dir) and not os.path.islink(file_or_dir):
                self.del_dir(file_or_dir) #it's a directory recursive call to function again
            else:
                try:
                    os.remove(file_or_dir) #it's a file, delete it
                except Exception, e:
                    #probably failed because it is not a normal file
                    raise w3afException('An exception was raised while removing the old database: ' + str(e) )
        os.rmdir(path) #delete the directory here

    def debug(self, msgString, newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        '''
        m = message( 'debug', self._cleanString(msgString), time.time(), newLine )
        self._addToQueue( m )
    
    def information(self, msgString , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        ''' 
        m = message( 'information', self._cleanString(msgString), time.time(), newLine )
        self._addToQueue( m )

    def error(self, msgString , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        m = message( 'error', self._cleanString(msgString), time.time(), newLine )
        self._addToQueue( m )

    def vulnerability(self, msgString , newLine=True, severity=severity.MEDIUM ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        m = message( 'vulnerability', self._cleanString(msgString), time.time(), newLine )
        m.setSeverity( severity )
        self._addToQueue( m )
        
    def console( self, msgString, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        m = message( 'console', self._cleanString(msgString), time.time(), newLine )
        self._addToQueue( m )
    
    def _addToQueue( self, m ):
        '''
        Adds a message object to the queue. If the queue isn't there, it creates one.
        '''
        self.queue.put( m )
    
    def logHttp( self, request, response):
        try:
            self._db_req_res.insert(response.id, request.getMethod(), request.getURI(), '1.1', request.dumpHeaders(), request.getData(), response.getCode(), response.getMsg(), response.dumpHeaders(), response.getBody(), response.getWaitTime() )
        except KeyboardInterrupt, k:
            raise k
        except Exception, e:
            om.out.error( 'Exception while inserting request/response to the database: ' + str(e) )
            raise e
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Saves messages to kb.kb.getData('gtkOutput', 'queue'), messages are saved in the form of objects. This plugin
        was created to be able to communicate with the gtkUi and should be enabled if you are using it.
        '''
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
    
    def setOptions( self, OptionList ):
        pass
        
class message:
    def __init__( self, type, msg , time, newLine=True ):
        '''
        @parameter type: console, information, vulnerability, etc
        @parameter msg: The message itself
        @parameter time: The time when the message was produced
        @parameter newLine: Should I print a newline ? True/False
        '''
        self._type = type
        self._msg = unicode(msg)
        self._newLine = newLine
        self._time = time
        self._severity = None
    
    def getSeverity( self ):
        return self._severity
        
    def setSeverity( self, s ):
        self._severity = s
    
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
