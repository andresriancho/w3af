"""
hpp.py
 
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

from io import StringIO
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
import w3af.core.data.parsers.parser_cache as parser_cache
from lxml import etree
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.parsers.url import URL
from w3af.core.data.kb.info_set import InfoSet


REFLECT_TOKEN = 'w3afHPPReflectToken'
FORGE_TOKEN = 'w3afHPPForgeToken'
EQUALITY_THRESHOLD = 0.95
#paramater precedence types
LAST = 'last occurance'
FIRST = 'first occurance'
CONCAT = 'concatination'
UNK = 'unknown'


class hpp(AuditPlugin):
    """
    Identify http parameter pollution vulnerabilities.
    """

    def __init__(self):
        AuditPlugin.__init__(self)
        self.parser = etree.HTMLParser(remove_blank_text=True, remove_comments=True)
        self.precedence = None
        self.rlink = ''


    def audit(self, freq, orig_response):
        """
        Tests an URL for HPP vulnerabilities.

        :param freq: A FuzzableRequest

        """

        rparams = {}

        if not orig_response.is_text_or_html():
            return

        if not orig_response.get_code() == 200:
            return
        method = freq.get_method()
        self._orig_uri = freq.get_uri()
        if method == 'GET':
            qs = freq.get_querystring()


        #finding reflected params
        for param in qs:
            value = qs[param][0]
            mutants = create_mutants(freq, [REFLECT_TOKEN],
                                     fuzzable_param_list= [param],
                                     mutant_tuple=(QSMutant,))
            mu = mutants[0]
            #first we send REFLECT_TOKEN
            resp = self._uri_opener.send_mutant(mu)
            try:
                dp = parser_cache.dpc.get_document_parser_for(resp)
            except BaseFrameworkException:
                return
            #do we have a reflection?

            body = self.strip_trash(resp.body)
            if not resp.get_code() == 200:
                #no need to seek reflection if it is not OK
                continue
            rp = self.find_reflection( dp, REFLECT_TOKEN)

            if not rp:
                # no reflection at all skip the parameter
                continue
            rparams[param] = rp
            # print "querystring parameter %s is reflected inside " \
            #       "a link HTML code" % param
            if self.precedence:
               continue

            #this hack is to make w3af send request with unencoded qs
            u =  str(mu.get_uri())
            ptest_url = URL(u.replace(REFLECT_TOKEN,
                                      value +'&'+param+'='+REFLECT_TOKEN))
            ptest_resp = self._uri_opener.GET(ptest_url)
            ptest_resp_code = ptest_resp.get_code()
            
            if not ptest_resp_code == 200:
                om.out.debug(u"Precedence check request to the uri %s "
                             u"failed! "
                             u"Got response code %s in response id %s\n"
                             u"Unable to continue HPP detection. "
                             u"Resource might be protected by a WAF,"
                             % (ptest_url, ptest_resp_code, ptest_resp.id))
                #no need to seek reflection if it is not OK
                continue

            ptest_body = self.strip_trash(ptest_resp.body)

            try:
                ptest_dp = parser_cache.dpc.get_document_parser_for(ptest_resp)
            except BaseFrameworkException:
                return

            if fuzzy_equal(self.strip_trash(orig_response.body),
                           ptest_body, EQUALITY_THRESHOLD):
                #confirm vuln
                if self.find_reflection( ptest_dp, value) == rp:
                    self.precedence =  FIRST
                    continue
            if fuzzy_equal(body, ptest_body, EQUALITY_THRESHOLD):
                #confirm vuln
                if self.find_reflection( ptest_dp, REFLECT_TOKEN) == rp:
                    self.precedence = LAST
                    continue
                #  report vulnerability
            try:
                reflection, link = self.find_reflection( ptest_dp, value, REFLECT_TOKEN)
            except TypeError:
                self.precedence == UNK

            if reflection == rp:
                self.precedence = CONCAT
                desc = u'Concatenation of values of the two input parameters ' \
                       u'with the same name \"%s\" detected inside HTML ' \
                       u'code of response body.\nThe request url was %s.\n' \
                       u'Got concatenated output reflected in this link %s\n' \
                       u'This \"feature\" may be used in different WAF ' \
                       u'bypassing techniques.'
                desc = desc % (param, ptest_url, link)
                print desc

                i = Info(u'Input concatenation detected', desc, ptest_resp.id,
                         self.get_name())
                i.set_url(ptest_url)
                self.kb_append(self, 'hpp', i)
                return



        if self.precedence == UNK:
            om.out.debug(u'Unable to determine precedence for HPP detection.'
                         u'Presumably not vulnerable to HPP.')

            return
#        print "Attack!!", self.precedence
        om.out.debug(u"Detected precedence is %s."
                     u"\nTrying pollution of the reflected parameters: %s."
                     % (self.precedence, rparams.keys()))
        #bulding payloads
        payloads = []
        vuln_params=[]
        for k,v in rparams.items():
            payloads.append(REFLECT_TOKEN+'&'+v+'='+FORGE_TOKEN)
        vtest_mutants = create_mutants(freq, payloads,
                                       fuzzable_param_list=rparams.keys(),
                                       mutant_tuple=(QSMutant,))
        for m in vtest_mutants:
            vtest_resp = self._uri_opener.send_mutant(m)
            try:
                vtest_dp = parser_cache.dpc.get_document_parser_for(vtest_resp)
            except BaseFrameworkException:
                return
            r =  self.find_reflection( vtest_dp, FORGE_TOKEN)
            if r:
                vuln_params.append(r)
                msg=u"value of parameter %s can be forged with " \
                    u"HPP attack using URL: %s, precedence is %s"
                msg = msg % (r, m.get_uri(), self.precedence)
                v=Vuln.from_mutant(u'HPP', desc=msg, mutant = m,
                                   plugin_name='hpp',response_ids=[],
                                   severity=severity.MEDIUM)
                v.set_url(self._orig_uri)
                v[HPPInfoSet.ITAG] = m.get_uri()
                # debug_msg = debug_msg % (rid, freq.get_uri())
                self.kb_append_uniq_group(self, 'hpp', v,
                                          group_klass=HPPInfoSet)

    def find_reflection(self, parser, pattern1, pattern2 = ''):
        #finds reflection of a string or two concatenated
        # strings in web page links or input parameters

        result = False
        #find reflection in links
        for ref in parser.get_references():
            if ref == []:
                continue
            qs = ref[0].get_querystring()
            for p in qs:
                if self.precedence == LAST and len(qs[p]) == 2:
                  v =  qs[p][1]
                else:
                  v =  qs[p][0]
                #looking for single reflection if only one pattern was entered
                if v == pattern1 and not pattern2:
                    result = p
                #or for concatenation of both were
                if v[:len(pattern1)] == pattern1 and \
                                v[-len(pattern2):] == pattern2:
                    result = p, ref[0]

        return result


    def strip_trash(self, doc):
        #stripping HTML comments

        tree   = etree.parse(StringIO(doc), self.parser)
        result = etree.tostring(tree.getroot(),
                                 pretty_print=True, method="html")
        return result


    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return u"""
        This plugin detects HTTP Parameter Pollution vulnerabilities.
        """

class HPPInfoSet(InfoSet):

        ITAG = 'hpp_link'
        TEMPLATE = (
            'The application is vulnarable to HPP. '
            ' {{ uris|length }} link may be polluted.'

        )