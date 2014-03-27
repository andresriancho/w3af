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
import threading

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.misc.decorators import retry
from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.data.request.variant_identification import are_variants


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

    @retry(3)
    def get_original_response(self, fuzzable_request):
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
            
            try:
                orig_response = self.get_original_response(fuzzable_request)
                self.audit_with_copy(fuzzable_request, orig_response)
            except Exception, e:
                om.out.error(str(e))
            finally:
                self._store_kb_vulns = False
                
                new_vulnerabilities = self._newly_found_vulns
                self._newly_found_vulns = []
                
                return new_vulnerabilities

    def _audit_return_vulns_in_caller(self):
        """
        This is a helper method that returns True if the method audit_return_vulns
        is in the call stack.
        
        Please note that this method is *very* slow (because of the inspect
        module being slow) and should only be called when audit_return_vulns
        was previously called.
        """
        the_stack = inspect.stack()

        for _,_,_,function_name,_,_ in the_stack:
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
        
        super(AuditPlugin, self).kb_append_uniq(location_a, location_b, info)
        
    def kb_append(self, location_a, location_b, info):
        """
        kb.kb.append a vulnerability to the KB
        """
        if self._store_kb_vulns:
            if self._audit_return_vulns_in_caller():
                self._newly_found_vulns.append(info)
        
        super(AuditPlugin, self).kb_append(location_a, location_b, info)

    def audit_with_copy(self, fuzzable_request, orig_resp):
        """
        :param freq: A FuzzableRequest
        :param orig_resp: The HTTP response we get from sending the freq
        
        Copy the FuzzableRequest before auditing.

        I copy the fuzzable request, to avoid cross plugin contamination.
        In other words, if one plugins modified the fuzzable request object
        INSIDE that plugin, I don't want the next plugin to suffer from that.
        """
        return self.audit(fuzzable_request.copy(), orig_resp)

    def audit(self, freq, orig_resp):
        """
        The freq is a FuzzableRequest that is going to be modified and sent.

        This method MUST be implemented on every plugin.

        :param freq: A FuzzableRequest
        :param orig_resp: The HTTP response we get from sending the freq
        """
        msg = 'Plugin is not implementing required method audit'
        raise NotImplementedError(msg)

    def _has_bug(self, fuzz_req, varname='', pname='', kb_varname=''):
        return not self._has_no_bug(fuzz_req, varname, pname, kb_varname)

    def _has_no_bug(self, fuzz_req, varname='', pname='', kb_varname=''):
        """
        Test if the current combination of `fuzz_req`, `varname` hasn't
        already been reported to the knowledge base.

        :param fuzz_req: A FuzzableRequest like object.
        :param varname: Typically the name of the injection parameter.
        :param pname: The name of the plugin that presumably reported
            the vulnerability. Defaults to self.name.
        :param kb_varname: The name of the variable in the kb, where
            the vulnerability was saved. Defaults to self.name.
        """
        with self._plugin_lock:
            if not varname:
                if hasattr(fuzz_req, 'get_var'):
                    varname = fuzz_req.get_var()
                else:
                    raise ValueError("Invalid arg 'varname': %s" % varname)

            pname = pname or self.get_name()
            kb_varname = kb_varname or pname
            vulns = kb.kb.get(pname, kb_varname)

            for vuln in vulns:
                if vuln.get_var() == varname and\
                fuzz_req.get_dc().keys() == vuln.get_dc().keys() and\
                are_variants(vuln.get_uri(), fuzz_req.get_uri()):
                    return False
                
            return True

    def get_type(self):
        return 'audit'
