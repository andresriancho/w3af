'''
baseAuditPlugin.py

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
import core.data.kb.knowledgeBase as kb

from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.basePlugin import basePlugin
from core.data.request.variant_identification import are_variants


class baseAuditPlugin(basePlugin):
    '''
    This is the base class for audit plugins, all audit plugins should inherit
    from it and implement the following methods :
        1. audit(...)
        
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        basePlugin.__init__( self )
        self._uri_opener = None

    # FIXME: This method is awful and returns LOTS of false positives
    def audit_wrapper( self, fuzzable_request ):
        '''
        Receives a fuzzable_request and forwards it to the internal method
        audit()
        
        @parameter fuzzable_request: A fuzzable_request instance
        '''
        # I copy the fuzzable request, to avoid cross plugin contamination
        # in other words, if one plugin modified the fuzzable request object
        # INSIDE that plugin, I don't want the next plugin to suffer from that
        fuzzable_request_copy = fuzzable_request.copy()
        
        # These lines were added because we need to return the new vulnerabilities found by this
        # audit plugin, and I don't want to change the code of EVERY plugin!
        before_vuln_dict = kb.kb.getData( self )
        
        self.audit( fuzzable_request_copy )
        
        after_vuln_dict = kb.kb.getData( self )
        
        # Now I get the difference between them:
        before_list = []
        after_list = []
        for var_name in before_vuln_dict:
            for item in before_vuln_dict[var_name]:
                before_list.append(item)
        
        for var_name in after_vuln_dict:
            for item in after_vuln_dict[var_name]:
                after_list.append(item)
        
        new_ones = after_list[len(before_list)-1:]
        
        # And return it,
        return new_ones
        
    def audit( self, freq ):
        '''
        The freq is a fuzzable_request that is going to be modified and sent.
        
        This method MUST be implemented on every plugin.
        
        @param freq: A fuzzable_request
        '''
        raise w3afException('Plugin is not implementing required method audit' )
    
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
                if hasattr(fuzz_req, 'getVar'):
                    varname = fuzz_req.getVar()
                else:
                    raise ValueError, "Invalid arg 'varname': %s" % varname
            
            pname = pname or self.getName()
            kb_varname = kb_varname or pname
            vulns = kb.kb.getData(pname, kb_varname)
    
            for vuln in vulns:
                if (vuln.getVar() == varname and
                fuzz_req.getDc().keys() == vuln.getDc().keys() and
                are_variants(vuln.getURI(), fuzz_req.getURI())):
                    return False
            return True
        
    def getType( self ):
        return 'audit'