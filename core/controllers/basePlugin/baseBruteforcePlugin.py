'''
baseBruteforcePlugin.py

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


from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.bruteforce.bruteforcer import bruteforcer
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.data.request.frFactory import createFuzzableRequests
import core.data.kb.knowledgeBase as kb
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import os.path


class baseBruteforcePlugin(baseAuditPlugin):
    '''
    This plugin is a superclass for plugins that want to bruteforce any type of login.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        self._alreadyTested = []
        
        # Config params
        self._usersFile = 'core'+os.path.sep+'controllers'+os.path.sep+'bruteforce'+os.path.sep+'users.txt'
        self._passwdFile = 'core'+os.path.sep+'controllers'+os.path.sep+'bruteforce'+os.path.sep+'passwords.txt'
        self._useMailUsers = True
        self._useSvnUsers = True
        self._stopOnFirst = True
        self._passEqUser = True
        self._l337_p4sswd = True
        self._useMails = True
        self._useProfiling = True
        self._profilingNumber = 50
        
        # Internal vars
        self._found = False
        self._alreadyReported = []
        
        self._bruteforcer = bruteforcer()

    def _initBruteforcer( self, url ):
        self._bruteforcer.setURL( url )
        self._bruteforcer.setUseMailUsers( self._useMailUsers )
        self._bruteforcer.setUseMails( self._useMails )
        self._bruteforcer.setUseProfiling( self._useProfiling )
        self._bruteforcer.setProfilingNumber( self._profilingNumber )
        self._bruteforcer.setUseSvnUsers( self._profilingNumber )
        self._bruteforcer.setLeetPasswd( self._l337_p4sswd )
        self._bruteforcer.init()
    
    def _fuzzRequests(self, freq ):
        '''
        This method is the entry point of the plugin.
        
        THIS METHOD MUST BE IMPLEMENTED BY EVERY BRUTEFORCE PLUGIN!
        
        @param freq: A fuzzable_request
        '''
        raise w3afException('Bruteforce plugins MUST override method _fuzzRequests.')
    
    def bruteforce_wrapper( self, fuzzable_request ):
        self.audit_wrapper( fuzzable_request.copy() )
        
        res = []
        for v in kb.kb.getData( self.getName(), 'auth' ):
            if v.getURL() not in self._alreadyReported:
                self._alreadyReported.append( v.getURL() )
                res.extend( createFuzzableRequests(v['response']) )
        return res
    
    def _bruteforce( self, url, combinations ):
        '''
        @parameter url: A string representation of an URL
        @parameter combinations: A list of tuples with (user,pass)
        '''
        targs = (url,combinations)
        self._tm.startFunction( target=self._bruteWorker, args=targs , ownerObj=self )
    
    def end( self ):
        self._tm.join( self )
            
    def _bruteWorker( self, url, combinations ):
        '''
        This is the method that sends the request to the remote server.
        
        @parameter url: A string representation of an URL
        @parameter combinations: A list of tuples with (user,pass)
        '''
        raise w3afException('Bruteforce plugins MUST override method _bruteWorker.')            
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Users file to use in bruteforcing'
        o1 = option('usersFile', self._usersFile, d1, 'string')
        
        d2 = 'Passwords file to use in bruteforcing'
        o2 = option('passwdFile', self._passwdFile, d2, 'string')
        
        d3 = 'This indicates if we will use usernames from emails collected by w3af plugins in bruteforce.'
        o3 = option('useMailUsers', self._useMailUsers, d3, 'boolean')
        
        d4 = 'This indicates if we will use usernames from SVN headers collected by w3af plugins in bruteforce.'
        o4 = option('useSvnUsers', self._useSvnUsers, d4, 'boolean')
        
        d5 = 'This indicates if the bruteforce should stop after finding the first correct user and password.'
        o5 = option('stopOnFirst', self._stopOnFirst, d5, 'boolean')
        
        d6 = 'This indicates if the bruteforce should try password equal user in logins.'
        o6 = option('passEqUser', self._passEqUser, d6, 'boolean')
        
        d7 = 'This indicates if the bruteforce should try l337 passwords'
        o7 = option('useLeetPasswd', self._l337_p4sswd, d7, 'boolean')
        
        d8 = 'This indicates if the bruteforcer should use usernames collected by w3af plugins.'
        o8 = option('useMails', self._useMails, d8, 'boolean')
        
        d9 = 'This indicates if the bruteforce should use password profiling to collect new passwords.'
        o9 = option('useProfiling', self._useProfiling, d9, 'boolean')
        
        d10 = 'This indicates how many passwords from profiling will be used.'
        o10 = option('profilingNumber', self._profilingNumber, d10, 'integer')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6)
        ol.add(o7)
        ol.add(o8)
        ol.add(o9)
        ol.add(o10)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._usersFile = optionsMap['usersFile'].getValue()
        self._stopOnFirst = optionsMap['stopOnFirst'].getValue()
        self._passwdFile = optionsMap['passwdFile'].getValue()
        self._passEqUser = optionsMap['passEqUser'].getValue()
        self._l337_p4sswd = optionsMap['useLeetPasswd'].getValue()
        self._useMailUsers = optionsMap['useMailUsers'].getValue()
        self._useSvnUsers = optionsMap['useSvnUsers'].getValue()
        self._useMails = optionsMap['useMails'].getValue()
        self._useProfiling = optionsMap['useProfiling'].getValue()
        self._profilingNumber = optionsMap['profilingNumber'].getValue()
        

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['grep.passwordProfiling','grep.getMails']

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin bruteforces form authentication logins.
        
        Nine configurable parameters exist:
            - usersFile
            - stopOnFirst
            - passwdFile
            - passEqUser
            - useLeetPasswd
            - useMailUsers
            - useSvnUsers
            - useMails
            - useProfiling
            - profilingNumber
        
        This plugin will take users from the file pointed by "usersFile", mail users found on the site ( if "useMailUsers" is
        set to True ), mails found on the site ( if "useMails" is set to True ), and svn users found on the site ( if "useSvnUsers"
        is set to True ).
        
        This plugin will take passwords from the file pointed by "passwdFile" and the result of the password profiling plugin 
        ( if "useProfiling" is set to True). The profilingNumber sets the number of results from the password profiling plugin
        to use in the password field.
        
        The "stopOnFirst" parameter indicates if the bruteforce will stop when finding the first valid credentials or not.
        '''
    
    def getType( self ):
        return 'bruteforce'
