'''
xss.py

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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants, createRandAlNum
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import core.data.constants.browsers as browsers


class xss(baseAuditPlugin):
    '''
    Find cross site scripting vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Some internal variables to keep track of remote web application sanitization
        self._fuzzableRequests = []
        self._xssMutants = []
        self._special_characters = ['<', '>', '"', "'", '(', ')']
        
        # User configured parameters
        self._check_stored_xss = True
        self._number_of_stored_xss_checks = 3
        
        # Used in the message
        self._xss_tests_length = len( self._get_xss_tests() )
        
    def audit(self, freq ):
        '''
        Tests an URL for XSS vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'Xss plugin is testing: ' + freq.getURL() )
        
        # Save it here, so I can search for permanent XSS
        self._fuzzableRequests.append( freq )
        
        # This list is just to test if the parameter is echoed back
        fake_mutants = createMutants( freq , ['', ] )
        for mutant in fake_mutants:
            # verify if the variable we are fuzzing is actually being echoed back
            if self._is_echoed( mutant ):
                # Search for reflected XSS
                self._search_reflected_xss(mutant)
                # And also check stored
                self._search_stored_xss(mutant)
                
            elif self._check_stored_xss:
                # Search for permanent XSS
                self._search_stored_xss(mutant)
                
    def _search_reflected_xss(self, mutant):
        '''
        Analyze the mutant for reflected XSS. We get here because we already verified and the
        parameter is being echoed back.
        
        @parameter mutant: A mutant that was used to test if the parameter was echoed back or not
        @return: None
        '''
        # Verify what characters are allowed
        try:
            allowed_chars = self._get_allowed_chars(mutant)
        except w3afException:
            # If something fails, every char is allowed
            allowed_chars = self._special_characters[:]
        
        # Filter the tests based on the knowledge we got from the previous test
        orig_xss_tests = self._get_xss_tests()
        filtered_xss_tests = []
        for xss_string, affected_browsers in orig_xss_tests:
            for char in self._special_characters:
                all_allowed = True
                if char in xss_string and not char in allowed_chars:
                    all_allowed = False
                    break
            # Decide wether to send the test or not
            if all_allowed:
                filtered_xss_tests.append((xss_string, affected_browsers))
        
        # Get the strings only
        xss_strings = [ i[0] for i in filtered_xss_tests ]
        mutant_list = createMutants( mutant.getFuzzableReq() , xss_strings , \
                                                    fuzzableParamList=[mutant.getVar(), ])

        # In the mutant, we have to save which browsers are vulnerable to that specific string
        for mutant in mutant_list:
            for xss_string, affected_browsers in filtered_xss_tests:
                if xss_string in mutant.getModValue():
                    mutant.affected_browsers = affected_browsers

        for mutant in mutant_list:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'xss' , 'xss', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
                
        self._tm.join( self )
    
    def _get_allowed_chars(self, mutant):
        '''
        These are the special characters that are tested:
            ['<', '>', '"', "'", '(', ')']
        
        I'm aware that this doesn't work if the filter also filters by length.
        The idea of this method is to reduce the amount of tests to be performed, if I start
        testing each char separately, I loose that performance enhancement that I want to
        get.
        
        @return: A list with the special characters that are allowed by the XSS filter
        '''
        # Create a random number and assign it to the mutant modified parameter
        rndNum = str( createRandAlNum( 4 ) )
        oldValue = mutant.getModValue() 
        
        joined_list = rndNum.join(self._special_characters)
        list_delimiter = str( createRandAlNum( 5 ) )
        joined_list = list_delimiter + joined_list + list_delimiter
        mutant.setModValue(joined_list)
        
        # send
        response = self._sendMutant( mutant, analyze=False )
        
        # restore the mutant values
        mutant.setModValue(oldValue)
        
        # Analyze the response
        allowed = []
        if response.getBody().count(list_delimiter) == 2:
            start = response.getBody().find(list_delimiter) 
            end = response.getBody().find(list_delimiter, start+1)
            the_list = response.getBody()[start+len(list_delimiter):end]
            split_list = the_list.split(rndNum)
            for i, char in enumerate(split_list):
                if char == self._special_characters[i]:
                    allowed.append(char)
        else:
            raise w3afException('The delimiter was not echoed back!')
        
        if allowed == self._special_characters:
            om.out.debug('All special characters are allowed.')
        
        return allowed
                
    def _search_stored_xss(self, mutant):
        '''
        Analyze the mutant for stored XSS. We get here because we already verified and the
        parameter is NOT being echoed back.
        
        @parameter mutant: A mutant that was used to test if the parameter was echoed back or not
        @return: None
        '''
        xss_tests = self._get_xss_tests()
        xss_tests = xss_tests[:self._number_of_stored_xss_checks]
        
        # Get the strings only
        xss_strings = [ i[0] for i in xss_tests ]
        # And now replace the alert by fake_alert; I don't want to break web applications
        xss_strings = [ xss_test.replace('alert', 'fake_alert') for xss_test in xss_strings ]
        
        mutant_list = createMutants( mutant.getFuzzableReq() , xss_strings , \
                                                    fuzzableParamList=[mutant.getVar(), ])
        
        # In the mutant, we have to save which browsers are vulnerable to that specific string
        for mutant in mutant_list:
            for xss_string, affected_browsers in xss_tests:
                if xss_string.replace('alert', 'fake_alert') in mutant.getModValue():
                    mutant.affected_browsers = affected_browsers

        for mutant in mutant_list:
            targs = (mutant,)
            self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
            
        self._tm.join( self )
        
    def _get_xss_tests( self ):
        '''
        Does a select to the DB for a list of XSS strings that will be tested agains the site.
        
        @return: A list of tuples with all XSS strings to test and the browsers in which they work. 
        Example: [ ('<>RANDOMIZE', ['Internet Explorer']) ]
        '''
        xss_tests = []
        
        #
        #   TODO: with these xss tests, and the rest of the plugin as it is, w3af has false negatives
        #    in the case in which we're already controlling something that is written inside <script></script>
        #    tags.
        #
        
        
        # The number 2 is to inject in stored xss and not "letting the user know we are testing 
        # the site". And also please note that I don't have this: alert2('abc'); this "failure" will
        # let me find XSS in web applications that have magic_quotes enabled and will also 
        # "double" invalidate the JS code, because RANDOMIZE will be replaced by something
        # like ecd6c00b7 and that will be an undefined variables.
        
        # I use SCrIPT instead of script of SCRIPT, just because there are some programmers that
        # use blacklists that have those words, and they may be doing the comparison with a case
        # sensitive function (if 'script' in user_input...
        # if 'SCRIPT' in user_input)
        xss_tests.append(('<SCrIPT>alert("RANDOMIZE")</SCrIPT>', [browsers.ALL, ]))
        
        # No quotes, with tag
        xss_tests.append(("<ScRIPT>a=/RANDOMIZE/\nalert(a.source)</SCRiPT>", [browsers.ALL, ]))
        xss_tests.append(("<ScRIpT>alert(String.fromCharCode(RANDOMIZE))</SCriPT>",
                [browsers.ALL, ]))
        xss_tests.append(("'';!--\"<RANDOMIZE>=&{()}", [browsers.ALL, ]))
        xss_tests.append(("<ScRIPt SrC=http://RANDOMIZE/x.js></ScRIPt>", [browsers.ALL, ]))
        xss_tests.append(("<ScRIPt/XSS SrC=http://RANDOMIZE/x.js></ScRIPt>", [browsers.ALL, ]))
        xss_tests.append(("<ScRIPt/SrC=http://RANDOMIZE/x.js></ScRIPt>", 
                [browsers.INTERNET_EXPLORER_6, browsers.INTERNET_EXPLORER_7,
                browsers.NETSCAPE_IE, browsers.FIREFOX, browsers.NETSCAPE_G]))
        
        # http://secunia.com/advisories/9716/
        # ASP.NET bypass
        xss_tests.append(('<\0SCrIPT>alert("RANDOMIZE")</SCrIPT>',
                [browsers.INTERNET_EXPLORER_6, browsers.NETSCAPE_IE]))
        # This one only works in IE
        xss_tests.append(('<SCR\0IPt>alert("RANDOMIZE")</Sc\0RIPt>',
                [browsers.INTERNET_EXPLORER_6, browsers.INTERNET_EXPLORER_7, browsers.NETSCAPE_IE]))
                
        xss_tests.append(("<IFRAME SRC=\"javascript:alert('RANDOMIZE');\"></IFRAME>", [browsers.ALL, ]))
        
        # IE only
        xss_tests.append(('</A/style="xss:exp/**/ression(alert(\'XSS\'))">',
                [browsers.INTERNET_EXPLORER_6, browsers.INTERNET_EXPLORER_7]))

        # Javascript
        xss_tests.append(('jAvasCript:alert("RANDOMIZE");',
                [browsers.INTERNET_EXPLORER_6, browsers.NETSCAPE_IE, browsers.OPERA]))
        xss_tests.append(('javas\tcript:alert("RANDOMIZE");',
                [browsers.INTERNET_EXPLORER_6, browsers.NETSCAPE_IE, browsers.OPERA]))
        xss_tests.append(('javas&#x09;cript:alert("RANDOMIZE");',
                [browsers.INTERNET_EXPLORER_6, browsers.NETSCAPE_IE, browsers.OPERA]))
        xss_tests.append(('javas\0cript:alert("RANDOMIZE");',
                [browsers.INTERNET_EXPLORER_6, browsers.NETSCAPE_IE]))
        
        # I need to identify everything I send to the web app
        rnd_value = createRandAlNum(4)

        xss_tests = [ (x[0].replace( "RANDOMIZE", rnd_value ), x[1]) for x in xss_tests ]

        return xss_tests
    
    def _is_echoed( self, mutant ):
        '''
        Verify if the parameter we are fuzzing is really being echoed back in the
        HTML response or not. If it isn't echoed there is no chance we are going to
        find a reflected XSS here.
        
        Also please note that I send a random alphanumeric value, and not a numeric
        value, because even if the number is echoed back (and only numbers are echoed
        back by the application) that won't be of any use in the XSS detection.
        
        @parameter mutant: The request to send.
        @return: True if variable is echoed
        '''
        # Create a random number and assign it to the mutant modified
        # parameter
        rndNum = str( createRandAlNum( 5 ) )
        oldValue = mutant.getModValue() 
        mutant.setModValue(rndNum)

        # send
        response = self._sendMutant( mutant, analyze=False )
        
        # restore the mutant values
        mutant.setModValue(oldValue)
        
        # Analyze and return response
        if rndNum in response:
            om.out.debug('The variable ' + mutant.getVar() + ' is being echoed back.' )
            return True
        else:
            om.out.debug('The variable ' + mutant.getVar() + ' is NOT being echoed back.' )
            return False
    
    def _analyzeResult( self, mutant, response ):
        '''
        Do we have a reflected XSS?
        
        @return: None, record all the results in the kb.
        '''
        # Add to the stored XSS checking
        self._addToPermanentXssChecking( mutant, response.id )
        
        #
        #   Only one thread at the time can enter here. This is because I want to report each
        #   vulnerability only once, and by only adding the "if self._hasNoBug" statement, that
        #   could not be done.
        #
        with self._plugin_lock:
            
            #
            #   I will only report the XSS vulnerability once.
            #
            if self._hasNoBug( 'xss' , 'xss' , mutant.getURL() , mutant.getVar() ):
                
                #   Internal variable for the analysis process
                vulnerable = False
                
                if mutant.getModValue() in response:
                    # Ok, we MAY have found a xss. Let's remove some false positives.
                    if mutant.getModValue().lower().count( 'javas' ):
                        # I have to check if javascript was written inside a SRC parameter of html
                        # afaik it is the only place this type (<IMG SRC="javascript:alert('XSS');">)
                        # of xss works.
                        if self._checkHTML( mutant.getModValue(), response ):
                            vulnerable = True
                    else:
                        # Not a javascript type of xss, it's a <SCRIPT>...</SCRIPT> type
                        vulnerable = True
                
                # Save it to the KB
                if vulnerable:                
                    v = vuln.vuln( mutant )
                    v.setPluginName(self.getName())
                    v.setId( response.id )
                    v.setName( 'Cross site scripting vulnerability' )
                    v.setSeverity(severity.MEDIUM)
                    msg = 'Cross Site Scripting was found at: ' + mutant.foundAt() 
                    msg += ' This vulnerability affects ' + ','.join(mutant.affected_browsers)
                    v.setDesc( msg )
                    v.addToHighlight( mutant.getModValue() )

                    kb.kb.append( self, 'xss', v )
    
    def _checkHTML( self, xss_string , response ):
        '''
        This function checks if the javascript XSS is going to work or not.
        
        Examples:
            Request: http://a.com/f.php?a=javascript:alert('XSS');
            HTML Response: <IMG SRC="javascript:alert('XSS');">
            _checkHTML returns True
        
            Request: http://a.com/f.php?a=javascript:alert('XSS');
            HTML Response: I love javascript:alert('XSS');
            _checkHTML returns False
        '''
        html_string = response.getBody()
        html_string = html_string.replace(' ','')
        xss_string = xss_string.replace(' ','')
        xss_tags = []
        xss_tags.extend(['<img', '<script'])
        
        where_xss_starts = html_string.find( xss_string )
        for tag in xss_tags:
            whereTagStarts = html_string.rfind( tag , 1, where_xss_starts )
            if whereTagStarts != -1:
                betweenImgAndXss = html_string[ whereTagStarts+1 : where_xss_starts ]
                if betweenImgAndXss.count('<') or betweenImgAndXss.count('>'):
                    return False
                else:
                    return True
            return False
        
    def _addToPermanentXssChecking( self, mutant, response_id ):
        '''
        This is used to check for permanent xss.
        
        @parameter mutant: The mutant objects
        @parameter response_id: The response id generated from sending the mutant
        
        @return: No value is returned.
        '''
        self._xssMutants.append( (mutant, response_id) )
        
    def end( self ):
        '''
        This method is called to check for permanent Xss. 
        Many times a xss isn't on the page we get after the GET/POST of the xss string.
        This method searches for the xss string on all the pages that are available.
        
        @return: None, vulns are saved to the kb.
        '''
        self._tm.join( self )
        if self._check_stored_xss:
            for fuzzable_request in self._fuzzableRequests:
                response = self._sendMutant(fuzzable_request, analyze=False,
                                            useCache=False)
                
                for mutant, mutant_response_id in self._xssMutants:
                    # Remember that httpResponse objects have a faster "__in__" than
                    # the one in strings; so string in response.getBody() is slower than
                    # string in response                    
                    if mutant.getModValue() in response:
                        
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setURL( fuzzable_request.getURL() )
                        v.setDc( fuzzable_request.getDc() )
                        v.setMethod( fuzzable_request.getMethod() )
                        
                        v['permanent'] = True
                        v['write_payload'] = mutant
                        v['read_payload'] = fuzzable_request
                        v.setName( 'Permanent cross site scripting vulnerability' )
                        v.setSeverity(severity.HIGH)
                        msg = 'Permanent Cross Site Scripting was found at: ' + response.getURL()
                        msg += ' . Using method: ' + v.getMethod() + '. The XSS was sent to the'
                        msg += ' URL: ' + mutant.getURL()+ '. ' + mutant.printModValue()
                        v.setDesc( msg )
                        v.setId( [response.id, mutant_response_id] )
                        v.addToHighlight( mutant.getModValue() )
                        kb.kb.append( self, 'xss', v )
                        break
        
        self.printUniq( kb.kb.getData( 'xss', 'xss' ), 'VAR' )

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Identify stored cross site scripting vulnerabilities'
        h1 = 'If set to True, w3af will navigate all pages of the target one more time,'
        h1 += ' searching for stored cross site scripting vulnerabilities.'
        o1 = option('checkStored', self._check_stored_xss, d1, 'boolean', help=h1)
        
        d2 = 'Set the amount of checks to perform for each fuzzable parameter.'
        d2 += ' Valid numbers: 1 to '+str(self._xss_tests_length)
        h2 = 'The XSS checks are ordered, if you set numberOfChecks to two, this plugin will only'
        h2 += ' send two XSS strings to each fuzzable parameter of the remote web application.'
        h2 += ' In most cases this setting is correct and you shouldn\'t change it. If you are'
        h2 += ' really determined and don\'t want to loose the 1% of the vulnerabilities that is'
        h2 += ' left out by this setting, feel free to set this number to '
        h2 += str(self._xss_tests_length)
        o2 = option('numberOfChecks', self._number_of_stored_xss_checks, d2, 'integer', help=h2)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._check_stored_xss = optionsMap['checkStored'].getValue()
        if optionsMap['numberOfChecks'].getValue() >= 1 and \
        optionsMap['numberOfChecks'].getValue() <= self._xss_tests_length:
            self._number_of_stored_xss_checks = optionsMap['numberOfChecks'].getValue()
        else:
            msg = 'Please enter a valid numberOfChecks value (1-'+str(self._xss_tests_length)+').'
            raise w3afException(msg)
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds Cross Site Scripting (XSS) vulnerabilities.
        
        Two configurable parameters exist:
            - checkStored
            - numberOfChecks
            
        To find XSS bugs the plugin will send a set of javascript strings to every parameter, and search for that input in
        the response. The parameter "checkStored" configures the plugin to store all data sent to the web application 
        and at the end, request all pages again searching for that input; the numberOfChecks determines how many
        javascript strings are sent to every injection point.
        '''
