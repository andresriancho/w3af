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

from core.controllers.basePlugin.baseBruteforcePlugin import baseBruteforcePlugin
from core.controllers.w3afException import w3afException
from core.data.dc.form import form as form
from core.controllers.misc.levenshtein import relative_distance
from core.data.fuzzer.fuzzer import createRandAlNum

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity


class formAuthBrute(baseBruteforcePlugin):
    '''
    Bruteforce HTML form authentication.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseBruteforcePlugin.__init__(self)
        
        # To store failed responses for later comparison
        self._login_failed_result_list = []
        
        self._user_field_name = None
        self._passwd_field_name = None
        
    def audit(self, freq ):
        '''
        Tries to bruteforce a form auth. This aint fast!
        
        @param freq: A fuzzableRequest
        '''
        if self._isLoginForm( freq ):
            if freq.getURL() not in self._alreadyTested:
                
                # Save it (we don't want dups!)
                self._alreadyTested.append( freq.getURL() )
                
                try:
                    self._user_field_name, self._passwd_field_name = self._getLoginFieldNames( freq )
                except w3afException, w3:
                    om.out.error( str(w3) )
                else:
                    # Init
                    self._initBruteforcer( freq.getURL() )
                    self._idFailedLoginPage( freq )
                
                    # Let the user know what we are doing
                    om.out.information('Found a form login. The action of the form is: "' + freq.getURL() +'".')
                    om.out.information('The username field to be used is: "' + self._user_field_name + '".')
                    om.out.information('The password field to be used is: "' + self._passwd_field_name + '".')
                    om.out.information('Starting form authentication bruteforce on URL: "' + freq.getURL() + '".')
                    
                    # Work
                    while not self._found or not self._stopOnFirst:
                        combinations = []
                        
                        for i in xrange( 30 ):
                            try:
                                combinations.append( self._bruteforcer.getNext() )
                            except w3afException:
                                om.out.information('No more user/password combinations available.')
                                return
                        
                        self._bruteforce( freq, combinations )
    
    
    def _idFailedLoginPage( self, freq ):
        '''
        Generate TWO different response bodies that are the result of failed logins.
        
        The first result is for logins with filled user and password fields; the second
        one is for a filled user and a blank passwd.
        '''
        data_container = freq.getDc()
        user_field, passwd_field = self._getLoginFieldNames( freq )
        
        # The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [ (createRandAlNum( 8 ), createRandAlNum( 8 ) ),
                    (createRandAlNum( 8 ), '' )]
        
        # The result is going to be stored here
        self._login_failed_result_list = []
        
        for user, passwd in tests:
            # setup the data_container
            data_container[ user_field ][0] = user
            data_container[ passwd_field ][0] = passwd
            freq.setDc( data_container )
            response = self._sendMutant( freq , analyze=False, grepResult=False )
            
            body = response.getBody()
            body = body.replace(user, '')
            body = body.replace(passwd, '')
            
            # Save it
            self._login_failed_result_list.append( body )
        
        # Now I perform a self test, before starting with the actual bruteforcing
        # The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [ (createRandAlNum( 8 ), createRandAlNum( 8 ) ),
                    (createRandAlNum( 8 ), '' )]
        
        for user, passwd in tests:
            # Now I do a self test of the result I just created.
            data_container[ user_field ][0] = user
            data_container[ passwd_field ][0] = passwd
            freq.setDc( data_container )
            response = self._sendMutant( freq , analyze=False, grepResult=False )
            
            body = response.getBody()
            body = body.replace(user, '')
            body = body.replace(passwd, '')
            
            if not self._matchesFailedLogin( body ):
                raise w3afException('Failed to generate a response that matches the failed login page.')
    
    
    def _matchesFailedLogin(self, response_body):
        '''
        @return: True if the response_body matches the previously created responses that
        are stored in self._login_failed_result_list.
        '''
        # In the ratio, 1 is completely equal.
        ratio0 = relative_distance( response_body, self._login_failed_result_list[0])
        ratio1 = relative_distance( response_body, self._login_failed_result_list[1])


        if ratio0 > 0.65 or ratio1 > 0.65:
            return True
        else:
            # I'm happy! The response_body IS NOT a failed login page.
            return False
        
    def _isLoginForm( self, freq ):
        '''
        @return: True if this fuzzableRequest is a loginForm.
        '''
        passwd = 0
        text = 0
        other = 0
        
        data_container = freq.getDc()
        
        if isinstance( data_container , form ):
            
            for parameter_name in data_container:

                if data_container.getType( parameter_name ).lower() == 'password':
                    passwd += 1
                
                elif data_container.getType( parameter_name ).lower() == 'text':
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
        data_container = freq.getDc()
        passwd = ''
        user_param_list = []
        
        for parameter_name in data_container:
                
            if data_container.getType( parameter_name ).lower() == 'password':
                passwd = parameter_name
            
            elif data_container.getType( parameter_name ).lower() == 'text':
                user_param_list.append( parameter_name )
        
        user = None
        #
        #   If there is more than one text field in the form, I'll choose the one that looks more
        #   like a "user field", based on the name. The other ones will be smartFilled (tm).
        #
        if len(user_param_list) == 1:
            user = user_param_list[0]
        
        else:
            for parameter_name in user:
                for common_user_param_name in ['usr', 'usuario', 'user', 'name', 'nombre']:
                    if common_user_param_name in parameter_name.lower():
                        user = parameter_name
                        break
                        
            if user == None:
                msg = 'There seems to be an HTML login form at "' + freq.getURL() + '", but it was'
                msg += ' impossible to determine which parameter should be used as the username'
                msg += ' during the bruteforce process.'
                raise w3afException( msg )
        
        return user, passwd
        
                
    def _bruteWorker( self, freq, combinations ):
        '''
        @parameter freq: A fuzzableRequest
        @parameter combinations: A list of tuples with (user,pass)
        '''
        data_container = freq.getDc()
        for combination in combinations:
            data_container[ self._user_field_name ][0] = combination[0]
            data_container[ self._passwd_field_name ][0] = combination[1]
            freq.setDc( data_container )
            
            # This "if" is for multithreading
            if not self._found or not self._stopOnFirst:
                response = self._sendMutant( freq, analyze=False, grepResult=False )
                
                body = response.getBody()
                body = body.replace(combination[0], '')
                body = body.replace(combination[1], '')
                
                if not self._matchesFailedLogin( body ):
                    self._found = True
                    v = vuln.vuln()
                    v.setURL( freq.getURL() )
                    v.setId(response.id)
                    v.setDesc( 'Found authentication credentials to: "'+ freq.getURL() +
                    '". A correct user and password combination is: ' + combination[0] + '/' + combination[1])
                    v['user'] = combination[0]
                    v['pass'] = combination[1]
                    v['response'] = response
                    v.setSeverity(severity.HIGH)
                    v.setName( 'Guessable credentials' )

                    # Save this for the bruteforce - discovery loop
                    headers = response.getHeaders()
                    additionalHeaders = []
                    for header_name in headers:
                        if 'cookie' in header_name.lower():
                            additionalHeaders.append( (header_name , headers[header_name]) )
                    v['additionalHeaders'] = additionalHeaders
                    
                    kb.kb.append( self , 'auth' , v )
                    om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                    break
                
