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
from __future__ import with_statement

import core.controllers.outputManager as om

from core.controllers.basePlugin.baseBruteforcePlugin import baseBruteforcePlugin
from core.controllers.w3afException import w3afException
from core.data.dc import form
from core.controllers.misc.levenshtein import relative_distance_ge
from core.data.fuzzer.fuzzer import createRandAlNum
from core.data.url.xUrllib import xUrllib

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
        
    def audit(self, freq):
        '''
        Tries to bruteforce a form auth. This aint fast!
        
        @param freq: A fuzzableRequest
        '''
        freq_url = freq.getURL()
        
        if self._isLoginForm(freq) and freq_url not in self._alreadyTested:
                
            # Save it (we don't want dups!)
            self._alreadyTested.append(freq_url)
            
            try:
                self._user_field_name, self._passwd_field_name = \
                                            self._getLoginFieldNames(freq)
            except w3afException, w3:
                om.out.error(str(w3))
            else:
                # Init
                self._initBruteforcer(freq_url)
                self._idFailedLoginPage(freq)
            
                # Let the user know what we are doing
                om.out.information('Found a form login. The action of the ' \
                                   'form is: "%s".' % freq_url)
                if self._user_field_name is not None:
                    om.out.information('The username field to be used is: ' \
                                       '"%s".' % self._user_field_name)
                om.out.information('The password field to be used is: "%s".' \
                                   % self._passwd_field_name)
                om.out.information('Starting form authentication bruteforce' \
                                   ' on URL: "%s".' % freq_url)
                
                # Work until something is found, or no more passwords
                # are available
                more_passwords = True
                
                while not (self._found and self._stopOnFirst) and \
                                                            more_passwords:
                    combinations = []
                    
                    for i in xrange(30):                            
                        #
                        # Two different cases, one for user/password forms, the
                        # other for password only forms.
                        #
                        if self._user_field_name is not None:
                            # user/pass form:
                            try:
                                combinations.append(self._bruteforcer.getNext())
                            except w3afException:
                                more_passwords = False
                                break
                        else:
                            # password only form:
                            try:
                                c = ['dummy-placeholder', \
                                        self._bruteforcer.getNextPassword()]
                                combinations.append(c)
                            except w3afException:
                                more_passwords = False
                                break

                    self._bruteforce(freq.copy(), combinations)                    
                
                # Wait for all _bruteWorker threads to finish.
                self._tm.join(self)
                
                # Report that we've finished.
                msg = 'Finished bruteforcing "'+ freq_url + '".'
                om.out.information( msg )


    def _idFailedLoginPage(self, freq):
        '''
        Generate TWO different response bodies that are the result of failed
        logins.
        
        The first result is for logins with filled user and password fields;
        the second one is for a filled user and a blank passwd.
        '''
        data_container = freq.getDc()
        data_container = self._true_extra_fields(data_container)
        
        # The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [(createRandAlNum(8), createRandAlNum(8)), 
                 (createRandAlNum(8), '')]
        
        # The result is going to be stored here
        self._login_failed_result_list = []
        
        for user, passwd in tests:
            # Setup the data_container
            # Remember that we can have password only forms!
            if self._user_field_name is not None:
                data_container[self._user_field_name][0] = user
            data_container[self._passwd_field_name][0] = passwd
            freq.setDc(data_container)
            
            response = self._sendMutant(freq, analyze=False, grepResult=False)
            
            body = response.getBody()
            body = body.replace(user, '')
            body = body.replace(passwd, '')
            
            # Save it
            self._login_failed_result_list.append(body)
        
        # Now I perform a self test, before starting with the actual bruteforcing
        # The first tuple is an invalid username and a password
        # The second tuple is an invalid username with a blank password
        tests = [(createRandAlNum(8), createRandAlNum(8)),
                 (createRandAlNum(8), '')]
        
        for user, passwd in tests:
            # Now I do a self test of the result I just created.
            #   Remember that we can have password only forms!
            if self._user_field_name is not None:
                data_container[self._user_field_name][0] = user
            data_container[self._passwd_field_name][0] = passwd
            freq.setDc(data_container)
            response = self._sendMutant(freq, analyze=False, grepResult=False)
            
            body = response.getBody()
            body = body.replace(user, '')
            body = body.replace(passwd, '')
            
            if not self._matchesFailedLogin(body):
                raise w3afException('Failed to generate a response that ' \
                                    'matches the failed login page.')
    
    def _matchesFailedLogin(self, resp_body):
        '''
        @return: True if the resp_body matches the previously created 
        responses that are stored in self._login_failed_result_list.
        '''
        lfrl = self._login_failed_result_list
        # 0.65 gives a good measure of similarity
        if relative_distance_ge(resp_body, lfrl[0], 0.65) or \
                relative_distance_ge(resp_body, lfrl[1], 0.65):
            return True
        else:
            # I'm happy! The response_body *IS NOT* a failed login page.
            return False
        
    def _isLoginForm(self, freq):
        '''
        @return: True if this fuzzableRequest is a loginForm.
        '''
        passwd = 0
        text = 0
        other = 0        
        data_container = freq.getDc()
        
        if isinstance(data_container, form.form):
            
            for parameter_name in data_container:

                if data_container.getType(parameter_name).lower() == 'password':
                    passwd += 1
                elif data_container.getType(parameter_name).lower() == 'text':
                    text += 1
                else:
                    other += 1
            
            #
            #   These are the ones we support
            #
            if text == 1 and passwd == 1:
                return True
            elif text == 0 and passwd == 1:
                msg = 'Identified a form with a password field and no username field: "'
                msg += freq.getURL() + '".'
                om.out.information( msg )
                return True
                
            #
            #   These we don't
            #
            elif passwd == 2:
                om.out.information( freq.getURL() + ' is a registration form.')
            elif passwd == 3:
                om.out.information( freq.getURL() + ' is a password change form.')
            return False
                
    def _getLoginFieldNames(self, freq):
        '''
        @return: The names of the form fields where to input the user and the password.
        Please remember that maybe user_parameter might be None, since we support
        password only login forms.
        '''
        data_container = freq.getDc()
        passwd_parameter = None
        user_parameter = None
        
        for parameter_name in data_container:
                
            if data_container.getType( parameter_name ).lower() == 'password':
                passwd_parameter = parameter_name
            
            elif data_container.getType( parameter_name ).lower() == 'text':
                user_parameter = parameter_name

        return user_parameter, passwd_parameter
    
    def _true_extra_fields(self, data_container):
        '''
        Some login forms have "extra" parameters. In some cases I've seen login forms
        that have an "I agree with the terms and conditions" checkbox. If w3af does not
        set that extra field to "true", even if I have the correct username and password
        combination, it won't perform a successful login.
        
        @return: A data_container that has all fields (other than the username and password)
        set to 1,
        '''
        for parameter_name in data_container:
            if parameter_name not in [self._user_field_name, self._passwd_field_name]:
                data_container[parameter_name ][0] = 1
        return data_container
        
    def _bruteWorker(self, freq, combinations):
        '''
        @parameter freq: A fuzzableRequest
        @parameter combinations: A list of tuples with (user,pass)
        '''
        
        def _doPOSTWithoutCookies(urlOpener, fuzz_req):
            url = fuzz_req.getURI()
            data = fuzz_req.getData()
            headers = fuzz_req.getHeaders()
            resp = urlOpener.POST(url, data, headers, grepResult=False,
                                  useCache=False)
            return resp
        
        data_container = freq.getDc()
        data_container = self._true_extra_fields(data_container)
        
        # Ok, now we start with the real bruteforcing!
        for combination in combinations:
            
            username = combination[0]
            userpwd = combination[1]
            
            # Remember that we can have password only forms!
            if self._user_field_name is not None:
                data_container[self._user_field_name][0] = username
            data_container[self._passwd_field_name][0] = userpwd
            freq.setDc(data_container)
            
            # This "if" is for multithreading
            if not self._found or not self._stopOnFirst:
                
                # TODO: This is a *hack*. This logic shouldn't be implemented
                # in the plugin but in xUrllib,
                urlOpener = xUrllib()
                resp = _doPOSTWithoutCookies(urlOpener, freq)
                
                body = resp.getBody()
                body = body.replace(username, '').replace(userpwd, '')
                
                with self._plugin_lock:                
                    if not self._matchesFailedLogin(body):
                        # Ok, this might be a valid combination.
                        # Now test with a new invalid password to ensure our
                        # previous possible found credentials are valid                        
                        data_container[self._passwd_field_name][0] = \
                                                            createRandAlNum(8)
                        freq.setDc(data_container)
                        verif_resp = _doPOSTWithoutCookies(xUrllib(), freq)
                        body = verif_resp.getBody()
                        body = body.replace(username, '').replace(userpwd, '')
    
                        if self._matchesFailedLogin(body):
                            self._found = True
                            freq_url = freq.getURL()
                            v = vuln.vuln()
                            v.setPluginName(self.getName())
                            v.setURL(freq.getURL())
                            v.setId(resp.id)
                            if self._user_field_name is not None:
                                msg = 'Found authentication credentials to: ' \
                                '"%s". A correct user and password combination ' \
                                'is: %s/%s' % (freq_url, username, userpwd)
                            else:
                                # There is no user field!
                                msg = 'Found authentication credentials to: ' \
                                '"%s". The correct password is: "%s".' \
                                % (freq_url, userpwd)
        
                            v.setDesc(msg)
                            v['user'] = username
                            v['pass'] = combination[1]
                            v['response'] = resp
                            v.setSeverity(severity.HIGH)
                            v.setName('Guessable credentials')
                            kb.kb.append(self, 'auth', v)
        
                            # Save cookies in the 'main' urlOpenet so the rest
                            # of active plugins use them. This is part of the
                            # previously mentioned hack.
                            headers = resp.getHeaders()
                            additionalHeaders = []
                            for header_name in headers:
                                if 'cookie' in header_name.lower():
                                    additionalHeaders.append(
                                            (header_name, headers[header_name]))                            
                            self._urlOpener.settings.setHeadersList(
                                                            additionalHeaders)

                            om.out.vulnerability(msg, severity=severity.HIGH)
                            return
