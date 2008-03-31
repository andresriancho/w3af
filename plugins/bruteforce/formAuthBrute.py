'''
formAuthBrute.py

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

import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseBruteforcePlugin import baseBruteforcePlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.kb.vuln as vuln
from core.data.url.xUrllib import xUrllib
from core.controllers.bruteforce.bruteforcer import bruteforcer
from core.data.dc.form import form as form
import re
from core.data.fuzzer.fuzzer import *
import core.data.constants.severity as severity

class formAuthBrute(baseBruteforcePlugin):
    '''
    Bruteforce HTML form authentication.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseBruteforcePlugin.__init__(self)
        
        # Note that \ are escaped first !
        self._metachars = ['\\', '.', '^', '$', '*', '+', '?', '{', '[', ']', \
        '|', '(', ')','..','\\d','\\D','\\s','\\S','\\w','\\W',\
        '\\A', '\\Z', '\\b','\\B']
        
    def _fuzzRequests(self, freq ):
        '''
        Tries to bruteforce a form auth. This aint fast!
        
        @param freq: A fuzzableRequest
        '''
        if self._isLoginForm( freq ):
            if freq.getURL() not in self._alreadyTested:
                om.out.information('Starting form authentication bruteforce on URL: ' + freq.getURL() )
                self._initBruteforcer( freq.getURL() )
                
                self._idFailedLoginPage( freq )
                
                self._userFieldName, self._passwdFieldName = self._getLoginFieldNames( freq )
                om.out.information('Found a form login. The action of the form is: ' + freq.getURL() )
                om.out.information('The username field to be used is: ' + self._userFieldName )
                om.out.information('The password field to be used is: ' + self._passwdFieldName )
                

                while not self._found or not self._stopOnFirst:
                    combinations = []
                    
                    for i in xrange( 30 ):
                        try:
                            combinations.append( self._bruteforcer.getNext() )
                        except w3afException, e:
                            om.out.information('No more user/password combinations available.')
                            self._alreadyTested.append( freq.getURL() )
                            return
                    
                    self._bruteforce( freq, combinations )
    
    
    def _idFailedLoginPage( self, freq ):
        '''
        Generate a re that matches a failed login.
        '''
        dc = freq.getDc()
        
        user, passwd = self._getLoginFieldNames( freq )
        dc[ user ] = createRandAlNum( 8 )
        dc[ passwd ] = createRandAlNum( 8 )
        freq.setDc( dc )
        response = self._sendMutant( freq , analyze=False, grepResult=False )
        
        # Escape special characters
        regexStr = response.getBody()
        for c in self._metachars:
            regexStr = regexStr.replace( c, '\\'+c )
        
        # For some reason I dont want to know about, ' ' (spaces) must be escaped also
        regexStr = regexStr.replace( ' ', '\\ ' )
        
        # If the failed login page showed the user or the passwd i sent, replace that with a ".*?"
        regexStr = regexStr.replace( dc[ user ], '.*?' )
        regexStr = regexStr.replace( dc[ passwd ], '.*?' )
        regexStr = '^' + regexStr + '$'
        self._regex = re.compile( regexStr )
        
        # Now I do a self test of the regex I just created.
        dc[ user ] = createRandAlNum( 8 )
        dc[ passwd ] = createRandAlNum( 8 )
        freq.setDc( dc )
        response = self._sendMutant( freq , analyze=False, grepResult=False )
        if not self._regex.search( response.getBody() ):
            raise w3afException('Failed to generate a regular expression that matches the failed login page.')
        
    
    def _isLoginForm( self, freq ):
        '''
        @return: True if this fuzzableRequest is a loginForm.
        '''
        passwd = 0
        text = 0
        other = 0
        
        dc = freq.getDc()
        
        if isinstance( dc , form ):
            
            for key in dc.keys():
                
                if dc.getType( key ).lower() == 'password':
                    passwd += 1
                
                elif dc.getType( key ).lower() == 'text':
                    text += 1
                
                else:
                    other += 1
                    
            if text == 1 and passwd == 1:
                return True
            elif text == 0 and passwd == 1:
                om.out.information( freq.getURL() + ' detected a form with a password field and no username field.')
            elif passwd == 2:
                om.out.information( freq.getURL() + ' is a registration form.')
            elif passwd == 3:
                om.out.information( freq.getURL() + ' is a password change form.')
            return False
                
    def _getLoginFieldNames( self, freq ):
        '''
        @return: The names of the form fields where to input the user and the password.
        '''
        dc = freq.getDc()
        user = passwd = ''
        
        for key in dc.keys():
                
            if dc.getType( key ).lower() == 'password':
                passwd = key
            
            elif dc.getType( key ).lower() == 'text':
                user = key
            
        return user, passwd
        
                
    def _bruteWorker( self, freq, combinations ):
        '''
        @parameter freq: A fuzzableRequest
        @parameter combinations: A list of tuples with (user,pass)
        '''
        dc = freq.getDc()
        for combination in combinations:
            dc[ self._userFieldName ] = combination[0]
            dc[ self._passwdFieldName ] = combination[1]
            freq.setDc( dc )
            
            # This "if" is for multithreading
            if not self._found or not self._stopOnFirst:
                response = self._sendMutant( freq, analyze=False, grepResult=False )
            
                if not self._regex.search( response.getBody() ):
                    self._found = True
                    v = vuln.vuln()
                    v.setURL( freq.getURL() )
                    v.setDesc( 'Found authentication credentials to: '+ freq.getURL() +
                    ' . A correct user and password combination is: ' + combination[0] + '/' + combination[1])
                    v['user'] = combination[0]
                    v['pass'] = combination[1]
                    v['response'] = response
                    v.setSeverity(severity.HIGH)
                    v.setName( 'Guessable credentials' )

                    # Save this for the bruteforce - discovery loop
                    headers = response.getHeaders()
                    additionalHeaders = []
                    for h in headers:
                        if 'cookie' in h:
                            additionalHeaders.append( (h , headers[h]) )
                    v['additionalHeaders'] = additionalHeaders
                    
                    kb.kb.append( self , 'auth' , v )
                    om.out.vulnerability( v.getDesc() )
                    break
                
