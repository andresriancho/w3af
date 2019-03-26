"""
audit_plugin.py

Copyright 2006 Andres Riancho

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
import inspect
import copy
import threading

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.controllers.misc.safe_deepcopy import safe_deepcopy
from w3af.core.controllers.exceptions import FourOhFourDetectionException
from w3af.core.data.fuzzer.utils import rand_alnum


class AuditPlugin(Plugin):
    """
    This is the base class for audit plugins, all audit plugins should inherit
    from it and implement the following methods :
        1. audit(...)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        Plugin.__init__(self)
        
        self._uri_opener = None
        self._store_kb_vulns = False
        self._audit_return_vulns_lock = threading.RLock()
        self._newly_found_vulns = []

    def get_original_response(self, fuzzable_request):

        data_container = fuzzable_request.get_raw_data()
        if hasattr(data_container, 'smart_fill'):
            fuzzable_request = copy.deepcopy(fuzzable_request)
            data_container.smart_fill()

        return self._uri_opener.send_mutant(fuzzable_request, grep=False,
                                            cache=False)

    def audit_return_vulns(self, fuzzable_request):
        """
        :param fuzzable_request: The fuzzable_request instance to analyze for
                                 vulnerabilities.
        :return: The vulnerabilities found when running this audit plugin.
        """
        with self._audit_return_vulns_lock:
            
            self._store_kb_vulns = True
            debugging_id = rand_alnum(8)
            
            try:
                orig_response = self.get_original_response(fuzzable_request)
                self.audit_with_copy(fuzzable_request, orig_response, debugging_id)
            except Exception, e:
                om.out.error(str(e))
            finally:
                self._store_kb_vulns = False
                
                new_vulnerabilities = self._newly_found_vulns
                self._newly_found_vulns = []
                
                return new_vulnerabilities

    def _audit_return_vulns_in_caller(self):
        """
        This is a helper method that returns True if the method
        audit_return_vulns is in the call stack.
        
        Please note that this method is *very* slow (because of the inspect
        module being slow) and should only be called when audit_return_vulns
        was previously called.
        """
        the_stack = inspect.stack()

        for _, _, _, function_name, _, _ in the_stack:
            if function_name == 'audit_return_vulns':
                return True
            
        return False

    def kb_append_uniq(self, location_a, location_b, info):
        """
        kb.kb.append_uniq a vulnerability to the KB
        """
        if self._store_kb_vulns:
            if self._audit_return_vulns_in_caller():
                self._newly_found_vulns.append(info)
        
        return super(AuditPlugin, self).kb_append_uniq(location_a, location_b, info)
        
    def kb_append(self, location_a, location_b, info):
        """
        kb.kb.append a vulnerability to the KB
        """
        if self._store_kb_vulns:
            if self._audit_return_vulns_in_caller():
                self._newly_found_vulns.append(info)
        
        super(AuditPlugin, self).kb_append(location_a, location_b, info)

    def audit_with_copy(self, fuzzable_request, orig_resp, debugging_id):
        """
        :param fuzzable_request: A FuzzableRequest
        :param orig_resp: The HTTP response we get from sending the freq
        :param debugging_id: A unique identifier for this call to audit().
                             See https://github.com/andresriancho/w3af/issues/16220

        Copy the FuzzableRequest before auditing.

        I copy the fuzzable request, to avoid cross plugin contamination.
        In other words, if one plugins modified the fuzzable request object
        INSIDE that plugin, I don't want the next plugin to suffer from that.
        """
        fuzzable_request = safe_deepcopy(fuzzable_request)

        try:
            return self.audit(fuzzable_request, orig_resp, debugging_id)
        except FourOhFourDetectionException, ffde:
            # We simply ignore any exceptions we find during the 404 detection
            # process. FYI: This doesn't break the xurllib error handling which
            # happens at lower layers.
            #
            # https://github.com/andresriancho/w3af/issues/8949
            om.out.debug('%s' % ffde)

    def audit(self, freq, orig_resp, debugging_id):
        """
        The freq is a FuzzableRequest that is going to be modified and sent.

        This method MUST be implemented on every plugin.

        :param freq: A FuzzableRequest
        :param orig_resp: The HTTP response we get from sending the freq
        :param debugging_id: A unique identifier for this call to audit()
                             See https://github.com/andresriancho/w3af/issues/16220
        """
        msg = 'Plugin is not implementing required method audit'
        raise NotImplementedError(msg)

    def _has_bug(self, fuzz_req, varname='', pname='', kb_varname=''):
        return not self._has_no_bug(fuzz_req, varname, pname, kb_varname)

    def _has_no_bug(self, mutant, varname='', pname='', kb_varname=''):
        """
        Test if the current combination of `fuzz_req`, `varname` hasn't
        already been reported to the knowledge base.

        :param mutant: A Mutant sub-class.
        :param varname: Typically the name of the injection parameter.
        :param pname: The name of the plugin that presumably reported
                      the vulnerability. Defaults to self.name.
        :param kb_varname: The name of the variable in the kb, where
                           the vulnerability was saved. Defaults to self.name.
        """
        pname = pname or self.get_name()
        kb_varname = kb_varname or pname
        varname = varname or mutant.get_token_name()

        query_location_tuple = (varname, mutant.get_url())

        for vuln in kb.kb.get_iter(pname, kb_varname):
            vuln_location_tuple = (vuln.get_token_name(), vuln.get_url())

            if vuln_location_tuple == query_location_tuple:
                return False

        return True

    def get_type(self):
        return 'audit'
