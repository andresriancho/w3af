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
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.w3afException import w3afException
from core.data.constants.browsers import (ALL, INTERNET_EXPLORER_6,
                                          INTERNET_EXPLORER_7, NETSCAPE_IE,
                                          FIREFOX, NETSCAPE_G, OPERA)
from core.data.fuzzer.fuzzer import createMutants, createRandAlNum
from core.data.options.option import option
from core.data.options.optionList import optionList
import core.controllers.outputManager as om
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln

import re


class xss(baseAuditPlugin):
    '''
    Find cross site scripting vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    # TODO: with these xss tests, and the rest of the plugin as
    # it is, w3af has false negatives in the case in which we're
    # already controlling something that is written inside
    # <script></script> tags.
    XSS_TESTS = (
        ('<SCrIPT>alert("RANDOMIZE")</SCrIPT>', (ALL,)),
        # No quotes, with tag
        ("<ScRIPT>a=/RANDOMIZE/\nalert(a.source)</SCRiPT>", (ALL,)),
        ("<ScRIpT>alert(String.fromCharCode(RANDOMIZE))</SCriPT>", (ALL,)),
        ("'';!--\"<RANDOMIZE>=&{()}", (ALL,)),
        ("<ScRIPt SrC=http://RANDOMIZE/x.js></ScRIPt>", (ALL,)),
        ("<ScRIPt/XSS SrC=http://RANDOMIZE/x.js></ScRIPt>", (ALL,)),
        ("<ScRIPt/SrC=http://RANDOMIZE/x.js></ScRIPt>",
           (INTERNET_EXPLORER_6, INTERNET_EXPLORER_7,
            NETSCAPE_IE, FIREFOX, NETSCAPE_G)),
        # http://secunia.com/advisories/9716/
        # ASP.NET bypass
        ('<\0SCrIPT>alert("RANDOMIZE")</SCrIPT>',
           (INTERNET_EXPLORER_6, NETSCAPE_IE)),
        # This one only works in IE
        ('<SCR\0IPt>alert("RANDOMIZE")</Sc\0RIPt>',
           (INTERNET_EXPLORER_6, INTERNET_EXPLORER_7, NETSCAPE_IE)),
        ("<IFRAME SRC=\"javascript:alert('RANDOMIZE');\"></IFRAME>", (ALL,)),
        # IE only
        ('</A/style="xss:exp/**/ression(alert(\'XSS\'))">',
           (INTERNET_EXPLORER_6, INTERNET_EXPLORER_7)),
        # Javascript
        ('jAvasCript:alert("RANDOMIZE");',
           (INTERNET_EXPLORER_6, NETSCAPE_IE, OPERA)),
        ('javas\tcript:alert("RANDOMIZE");',
           (INTERNET_EXPLORER_6, NETSCAPE_IE, OPERA)),
        ('javas&#x09;cript:alert("RANDOMIZE");',
           (INTERNET_EXPLORER_6, NETSCAPE_IE, OPERA)),
        ('javas\0cript:alert("RANDOMIZE");',
           (INTERNET_EXPLORER_6, NETSCAPE_IE))
    )

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Some internal variables to keep track of remote 
        # web application sanitization
        self._fuzzableRequests = []
        self._xssMutants = []
        self._special_characters = ['<', '>', '"', "'", '(', ')']
        
        # User configured parameters
        self._check_stored_xss = True
        self._number_of_stored_xss_checks = 3
        
        # Used in the message
        self._xss_tests_length = len(xss.XSS_TESTS)
        
    def audit(self, freq):
        '''
        Tests an URL for XSS vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug('XSS plugin is testing: ' + freq.getURL())
        
        # Save it here, so I can search for permanent XSS
        self._fuzzableRequests.append(freq)
        
        # This list is just to test if the parameter is echoed back
        fake_mutants = createMutants(freq, ['',])
        for mutant in fake_mutants:
            # verify if the variable we are fuzzing is actually being
            # echoed back
            if self._is_echoed(mutant):
                # Search for reflected XSS
                self._search_reflected_xss(mutant)
                # And also check stored
                self._search_stored_xss(mutant)
                
            elif self._check_stored_xss:
                # Search for permanent XSS
                self._search_stored_xss(mutant)
                
    def _search_reflected_xss(self, mutant):
        '''
        Analyze the mutant for reflected XSS. We get here because we
        already verified and the parameter is being echoed back.
        
        @parameter mutant: A mutant that was used to test if the parameter
            was echoed back or not
        '''
        # Verify what characters are allowed
        try:
            allowed_chars = self._get_allowed_chars(mutant)
        except w3afException:
            # If something fails, every char is allowed
            allowed_chars = self._special_characters[:]
        
        # Filter the tests based on the knowledge we got from the
        # previous test
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
        xss_strings = [i[0] for i in filtered_xss_tests]
        mutant_list = createMutants(
                            mutant.getFuzzableReq(),
                            xss_strings,
                            fuzzableParamList=[mutant.getVar()]
                            )

        # In the mutant, we have to save which browsers are vulnerable
        # to that specific string
        for mutant in mutant_list:
            for xss_string, affected_browsers in filtered_xss_tests:
                if xss_string in mutant.getModValue():
                    mutant.affected_browsers = affected_browsers

            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._has_no_bug(mutant):
                args = (mutant,)
                kwds = {'callback': self._analyze_result }
                self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                    kwds=kwds)
        self._join()
    
    def _get_allowed_chars(self, mutant):
        '''
        These are the special characters that are tested:
            ['<', '>', '"', "'", '(', ')']
        
        Notice that this doesn't work if the filter also filters
        by length. The idea of this method is to reduce the amount of
        tests to be performed, if each char is tested separately the
        wanted performance enhancement will be lost.
        
        @return: A list with the special characters that are allowed
            by the XSS filter
        '''
        # Create a random number and assign it to the mutant
        # modified parameter
        rndNum = str(createRandAlNum(2))
        oldValue = mutant.getModValue() 
        
        joined_list = rndNum.join(self._special_characters)
        list_delimiter = str(createRandAlNum(2))
        joined_list = list_delimiter + joined_list + list_delimiter
        mutant.setModValue(joined_list)
        
        # send
        response = self._uri_opener.send_mutant(mutant)
        
        # restore the mutant values
        mutant.setModValue(oldValue)
        
        # Analyze the response
        allowed = []
        body = response.getBody()

        # Create the regular expression
        joined_char_regex = rndNum.join( ['.{0,7}?'] * len(self._special_characters) )
        joined_re = list_delimiter + joined_char_regex + list_delimiter

        for match in re.findall(joined_re, body):
            match_without_lim = match[ len(list_delimiter) : -len(list_delimiter)]
            split_list = match_without_lim.split(rndNum)
            for char in split_list:
                if char in self._special_characters:
                    allowed.append(char)

        allowed = list(set(allowed))
        allowed.sort()
        self._special_characters.sort()
        disallowed = list( set(self._special_characters) - set(allowed) )

        if allowed == self._special_characters:
            om.out.debug('All XSS special characters are allowed: %s' % ''.join(allowed) ) 
        else:
            om.out.debug('Allowed XSS special characters: %s' % ''.join(allowed) )
            om.out.debug('Encoded/Removed XSS special characters: %s' % ''.join(disallowed) )  
        
        return allowed
                
    def _search_stored_xss(self, mutant):
        '''
        Analyze the mutant for stored XSS. We get here because we
        already verified and the parameter is NOT being echoed back.
        
        @parameter mutant: A mutant that was used to test if the
            parameter was echoed back or not
        '''
        xss_tests = self._get_xss_tests()
        xss_tests = xss_tests[:self._number_of_stored_xss_checks]
        
        # Get the strings only
        xss_strings = [i[0] for i in xss_tests]
        # And now replace the alert by fake_alert; I don't want to
        # break web applications
        xss_strings = [xss_test.replace('alert', 'fake_alert')
                        for xss_test in xss_strings]
        
        mutant_list = createMutants(
                            mutant.getFuzzableReq(),
                            xss_strings,
                            fuzzableParamList=[mutant.getVar()]
                            )
        
        # In the mutant, we have to save which browsers are vulnerable
        # to that specific string
        for mutant in mutant_list:
            for xss_string, affected_browsers in xss_tests:
                if xss_string.replace('alert', 'fake_alert') in \
                                                    mutant.getModValue():
                    mutant.affected_browsers = affected_browsers
                    
            if self._has_no_bug(mutant):
                args = (mutant,)
                kwds = {'callback': self._analyze_result }
                self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                    kwds=kwds)
                
        self._join()

    def _get_xss_tests(self):
        '''
        Does a select to the DB for a list of XSS strings that will be
        tested agains the site.
        
        @return: A list of tuples with all XSS strings to test and
            the browsers in which they work. 
        Example: [('<>RANDOMIZE', ['Internet Explorer'])]
        '''
        # Used to identify everything that is sent to the web app
        rnd_value = createRandAlNum(4)

        return [(x[0].replace("RANDOMIZE", rnd_value), x[1])
                    for x in xss.XSS_TESTS]
    
    def _is_echoed(self, mutant):
        '''
        Verify if the parameter we are fuzzing is really being echoed
        back in the HTML response or not. If it isn't echoed there is
        no chance we are going to find a reflected XSS here.
        
        Also please note that I send a random alphanumeric value, and
        not a numeric value, because even if the number is echoed back
        (and only numbers are echoed back by the application) that won't
        be of any use in the XSS detection.
        
        @parameter mutant: The request to send.
        @return: True if variable is echoed
        '''
        # Create a random number and assign it to the mutant modified
        # parameter
        rndNum = str(createRandAlNum(5))
        oldValue = mutant.getModValue() 
        mutant.setModValue(rndNum)

        # send
        response = self._uri_opener.send_mutant(mutant)
        
        # restore the mutant values
        mutant.setModValue(oldValue)
        
        # Analyze and return response
        res = rndNum in response
        om.out.debug('The variable %s is %sbeing echoed back.' %
                     (mutant.getVar(), '' if res else 'NOT '))
        return res
    
    def _analyze_result(self, mutant, response):
        '''
        Do we have a reflected XSS?
        
        @return: None, record all the results in the kb.
        '''
        # Add to the stored XSS checking
        self._addToPermanentXssChecking(mutant, response.id)
        
        with self._plugin_lock:
            
            mod_value = mutant.getModValue()
            
            #
            #   I will only report the XSS vulnerability once.
            #
            if self._has_no_bug(mutant):
                
                #   Internal variable for the analysis process
                vulnerable = False
                
                if mod_value in response:
                    # Ok, we MAY have found a xss. Let's remove some false positives.
                    if mod_value.lower().count('javas'):
                        # I have to check if javascript was written inside a SRC parameter of html
                        # afaik it is the only place this type (<IMG SRC="javascript:alert('XSS');">)
                        # of xss works.
                        if self._checkHTML(mod_value, response):
                            vulnerable = True
                    else:
                        # Not a javascript type of xss, it's a <SCRIPT>...</SCRIPT> type
                        vulnerable = True
                
                # Save it to the KB
                if vulnerable:                
                    v = vuln.vuln(mutant)
                    v.setPluginName(self.getName())
                    v.setId(response.id)
                    v.setName('Cross site scripting vulnerability')
                    v.setSeverity(severity.MEDIUM)
                    msg = 'Cross Site Scripting was found at: ' + mutant.foundAt() 
                    msg += ' This vulnerability affects ' + ','.join(mutant.affected_browsers)
                    v.setDesc(msg)
                    v.addToHighlight(mod_value)
                    kb.kb.append(self, 'xss', v)
    
    def _checkHTML(self, xss_string , response):
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
        html_string = html_string.replace(' ', '')
        xss_string = xss_string.replace(' ', '')
        xss_tags = []
        xss_tags.extend(['<img', '<script'])
        
        where_xss_starts = html_string.find(xss_string)
        for tag in xss_tags:
            whereTagStarts = html_string.rfind(tag , 1, where_xss_starts)
            if whereTagStarts != -1:
                betweenImgAndXss = html_string[whereTagStarts + 1 : where_xss_starts]
                if betweenImgAndXss.count('<') or betweenImgAndXss.count('>'):
                    return False
                else:
                    return True
            return False
        
    def _addToPermanentXssChecking(self, mutant, response_id):
        '''
        This is used to check for permanent xss.
        
        @parameter mutant: The mutant objects
        @parameter response_id: The response id generated from sending the mutant
        
        @return: No value is returned.
        '''
        self._xssMutants.append((mutant, response_id))
        
    def end(self):
        '''
        This method is called to check for permanent Xss. 
        Many times a xss isn't on the page we get after the GET/POST of
        the xss string. This method searches for the xss string on all
        the pages that are available.
        
        @return: None, vulns are saved to the kb.
        '''
        if self._check_stored_xss:
            for fuzzable_request in self._fuzzableRequests:
                response = self._uri_opener.send_mutant(fuzzable_request,
                                                         cache=False)

                for mutant, mutant_response_id in self._xssMutants:
                    # Remember that httpResponse objects have a faster "__in__" than
                    # the one in strings; so string in response.getBody() is slower than
                    # string in response                    
                    if mutant.getModValue() in response:
                        
                        v = vuln.vuln(mutant)
                        v.setPluginName(self.getName())
                        v.setURL(fuzzable_request.getURL())
                        v.setDc(fuzzable_request.getDc())
                        v.setMethod(fuzzable_request.getMethod())
                        
                        v['permanent'] = True
                        v['write_payload'] = mutant
                        v['read_payload'] = fuzzable_request
                        v.setName('Permanent cross site scripting vulnerability')
                        v.setSeverity(severity.HIGH)
                        msg = 'Permanent Cross Site Scripting was found at: ' + response.getURL()
                        msg += ' . Using method: ' + v.getMethod() + '. The XSS was sent to the'
                        msg += ' URL: ' + mutant.getURL() + '. ' + mutant.printModValue()
                        v.setDesc(msg)
                        v.setId([response.id, mutant_response_id])
                        v.addToHighlight(mutant.getModValue())

                        om.out.vulnerability(v.getDesc())
                        kb.kb.append(self, 'xss', v)
                        break
        
        self.printUniq(kb.kb.getData('xss', 'xss'), 'VAR')

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Identify stored cross site scripting vulnerabilities'
        h1 = 'If set to True, w3af will navigate all pages of the target one more time,'
        h1 += ' searching for stored cross site scripting vulnerabilities.'
        o1 = option('checkStored', self._check_stored_xss, d1, 'boolean', help=h1)
        
        d2 = 'Set the amount of checks to perform for each fuzzable parameter.'
        d2 += ' Valid numbers: 1 to ' + str(self._xss_tests_length)
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
        
    def setOptions(self, optionsMap):
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
            msg = 'Please enter a valid numberOfChecks value (1-' + str(self._xss_tests_length) + ').'
            raise w3afException(msg)
        
    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []

    def getLongDesc(self):
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
