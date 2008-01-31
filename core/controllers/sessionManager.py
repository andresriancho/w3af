'''
sessionManager.py

Copyright 2006 Andres Riancho

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
import os
try:
   import cPickle as pickle
except ImportError:
   import pickle
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
import copy

# only used for debugging memory problems of w3af
import core.controllers.misc.memoryUsage as memoryUsage

MAXUNSAVED = 5

class sessionManager:
    '''
    This class manages a session
    
    Pickle _sessionData on every call to save.
    unPickle _sessionData when initing with a filename as paremeter to __init__.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    ''' 
    
    def __init__( self ):
        self._sessionDirectory = 'sessions'
        self._sessionName = 'defaultSession'
        self._saveCount = 0
    
    def saveSession( self, sessionName='defaultSession' ):
        self._sessionName = sessionName
        cf.cf.save('sessionName', sessionName )
        self._sessionData = {}
    
    def loadSession( self, sessionName ):
        self._sessionName = sessionName
        # Load the session
        try:
            self._loadSession()
        except:
            raise
        else:
            self._loadKb()
            self._loadCf()
            cf.cf.save('sessionName', sessionName )
    
    def setSessionDir( self, sessionDirectory ):
        self._sessionDirectory = sessionDirectory
        
    def save( self, variable, value ):
        '''
        Saves the options to a file.
        
        @parameter variable: The variable that we want to save data to
        @parameter value: The value of that variable
        '''
        # This is called for debugging, no session manager logic here...
        memoryUsage.dumpMemoryUsage()
        
        #om.out.debug( 'Saving: ' + str(variable) )
        self._sessionData[ variable ] = value
        self._saveCount += 1
        if self._saveCount == MAXUNSAVED:
            # Save to disk
            self._saveSessionData()
            self._saveKbData()
            self._saveCfData()
            # Restore count
            self._saveCount = 0
            # Inform what i did
            om.out.debug('Written session to disk. This is done only after ' + str(MAXUNSAVED) + ' calls to save().')
        
    def getData( self, variable ):
        if variable in self._sessionData:
            #om.out.debug( 'I was saved: ' + str(variable) )
            return self._sessionData[ variable ]
        else:
            return None
    
    def _loadCf( self ):
        cf.cf = self._load( self._sessionName + '.cf' )
        
    def _loadKb( self ):
        kb.kb = self._load( self._sessionName + '.kb' )
        kb.kb.createLock()
        
    def _loadSession( self ):
        try:
            self._sessionData = self._load( self._sessionName + '.data' )
        except Exception, e:
            self._sessionData = {}
            om.out.error('\rFailed to load session file.')
            raise e
    
    def _load( self, fileName ):
        '''
        Loads an object from the fileName.
        
        @parameter fileName: The filename where the options are read.
        @return: An object instance.
        '''
        if not os.path.exists(self._sessionDirectory):
            raise w3afException('The session directory does not exist.')
        dirFname = os.path.join(self._sessionDirectory, fileName)
        try:
            file = open( dirFname, 'rb' )
        except IOError:
            raise w3afException('Could not open session file for reading, filename: ' + dirFname )
        else:
            try:
                try:
                    return pickle.load(file)
                except pickle.PicklingError, pe:
                    raise w3afException('The object cant be pickled. Error: ' + str(pe) )
            finally:
                file.close()
    
    def _saveKbData( self ):
        pickable = self._makePickableKB( kb.kb )
        # Now , save the kb to disk
        self._saveData( pickable , self._sessionName + '.kb' )
        
    def _saveCfData( self ):
        # Now , save the config to disk
        self._saveData( cf.cf , self._sessionName + '.cf' )
    
    def _saveSessionData( self ):
        pickable = self._makePickableData( self._sessionData )
        self._saveData(  pickable, self._sessionName + '.data' )
        
    def _saveData( self, data, fileName ):
        
        if fileName != None:
            if not os.path.exists(self._sessionDirectory):
                os.mkdir(self._sessionDirectory)
            sdf = os.path.join(self._sessionDirectory, fileName)
            try:
                file = open( sdf , 'w' )
            except IOError:
                raise w3afException('Could not open session file for writing. Session file: ' + sdf )
            else:
                try:
                    try:
                        pickle.dump( data , file )
                    except pickle.PicklingError, pe:
                        raise w3afException('The object cant be pickled. Error: ' + str(pe) )
                finally:
                    file.close()        
    
    def _makePickableKB( self, data ):
        '''
        Some plugins save data to the kb that cant be pickled (for example, error404page saves a instance method).
        So i remove the data from the kb AND also remove the entry from the self._sessionData that says : "error404Page" was
        already runned, dont run again.
        '''
        # Init some variables
        kbObj = data.dump()
        unpickableObjects = []
        unpickableAddresses = [ ('error404page','404'), ('gtkOutput','db'), ('gtkOutput','queue'), ('urls','urlQueue') ]
        
        # Clean the kbObj from the nasty unpickable Objects
        for key1 in kbObj:
            for key2 in kbObj[key1]:
                if (key1,key2) in unpickableAddresses:
                    unpickableObjects.append( (key1,key2,kbObj[key1][key2]) )
                    data.save( key1, key2, None )
        
        # Copy the pickable version
        data.destroyLock()
        res = copy.deepcopy( data )
        data.createLock()

        # Restore it...
        for key1, key2, obj in unpickableObjects:
            data.save(key1,key2, obj)
        
        return res
            
    def _makePickableData( self, data ):
        '''
        Some plugins save data to the kb that cant be pickled (for example, error404page saves a instance method).
        So i remove the data from the kb AND also remove the entry from the self._sessionData that says : "error404Page" was
        already runned, dont run again.
        '''
        res = data
        for i in data:
            if i[0] == 'error404page':
                tmp = copy.copy( res )
                tmp.pop( i )
                res = tmp
                
        return res
