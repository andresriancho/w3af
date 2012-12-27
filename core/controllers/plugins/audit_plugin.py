'''
AuditPlugin.py

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
import core.data.kb.knowledge_base as kb

from core.controllers.plugins.plugin import Plugin
from core.data.request.variant_identification import are_variants


class AuditPlugin(Plugin):
    '''
    This is the base class for audit plugins, all audit plugins should inherit
    from it and implement the following methods :
        1. audit(...)

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        Plugin.__init__(self)
        self._uri_opener = None

    # FIXME: This method is awful and returns LOTS of false positives. Only
    #        used by ./core/ui/gui/reqResViewer.py
    def audit_wrapper(self, fuzzable_request):
        '''
        Receives a FuzzableRequest and forwards it to the internal method
        audit()

        @param fuzzable_request: A fuzzable_request instance
        '''
        # These lines were added because we need to return the new vulnerabilities found by this
        # audit plugin, and I don't want to change the code of EVERY plugin!
        before_vuln_dict = kb.kb.get(self)

        self.audit_with_copy(fuzzable_request)

        after_vuln_dict = kb.kb.get(self)

        # Now I get the difference between them:
        before_list = []
        after_list = []
        for var_name in before_vuln_dict:
            for item in before_vuln_dict[var_name]:
                before_list.append(item)

        for var_name in after_vuln_dict:
            for item in after_vuln_dict[var_name]:
                after_list.append(item)

        new_ones = after_list[len(before_list) - 1:]

        # And return it,
        return new_ones

    def audit_with_copy(self, fuzzable_request):
        '''
        Copy the FuzzableRequest before auditing.

        I copy the fuzzable request, to avoid cross plugin contamination.
        In other words, if one plugins modified the fuzzable request object
        INSIDE that plugin, I don't want the next plugin to suffer from that.
        '''
        return self.audit(fuzzable_request.copy())

    def audit(self, freq):
        '''
        The freq is a FuzzableRequest that is going to be modified and sent.

        This method MUST be implemented on every plugin.

        @param freq: A FuzzableRequest
        '''
        msg = 'Plugin is not implementing required method audit'
        raise NotImplementedError(msg)

    def _has_bug(self, fuzz_req, varname='', pname='', kb_varname=''):
        return not self._has_no_bug(fuzz_req, varname, pname, kb_varname)

    def _has_no_bug(self, fuzz_req, varname='', pname='', kb_varname=''):
        '''
        Test if the current combination of `fuzz_req`, `varname` hasn't
        already been reported to the knowledge base.

        @param fuzz_req: A FuzzableRequest like object.
        @param varname: Typically the name of the injection parameter.
        @param pname: The name of the plugin that presumably reported
            the vulnerability. Defaults to self.name.
        @param kb_varname: The name of the variable in the kb, where
            the vulnerability was saved. Defaults to self.name.
        '''
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
                if (vuln.get_var() == varname and
                    fuzz_req.get_dc().keys() == vuln.get_dc().keys() and
                        are_variants(vuln.get_uri(), fuzz_req.get_uri())):
                    return False
            return True

    def get_type(self):
        return 'audit'
