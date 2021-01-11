"""
hpp.py
 
Copyright 2015 Andres Riancho
 
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

REFLECT_TOKEN = 'w3afHPPReflectToken'
FORGE_TOKEN = 'w3afHPPForgeToken'
EQUALITY_THRESHOLD = 0.95
# paramater precedence types
LAST = 'last occurance'
FIRST = 'first occurance'
CONCAT = 'concatenation'


def get_forgeable(reflection, prec):
    #this function returns list of querystring parameters which may be
    #forged provided precedence is prec
    r = []
    param, url = reflection
    qs = url.get_querystring()

    passed = 0
    for p in qs:
        if p == param:
            passed = 1
            continue
        if passed == 0 and prec == LAST:
            r += [p]
        if passed == 1 and prec == FIRST:
            r += [p]
    return r


def find_reflection(response, precedence, patterns):
    #finds reflection of a string or two concatenated
    # strings in web page links or input parameters
    if len(patterns) > 1:
        pattern1, pattern2 = patterns
    else:
        pattern1, pattern2 = patterns[0], None

    try:
        parser = parser_cache.dpc.get_document_parser_for(response)
    except BaseFrameworkException:
        return

    pattern1 = unicode(pattern1)
    result = []
    #find reflection in links
    for references in parser.get_references():
        for ref in references:
            if not ref:
                continue
            qs = ref.get_querystring()
            for p in qs:
                if precedence == LAST and len(qs[p]) == 2:
                    rv = qs[p][1]
                else:
                    rv = qs[p][0]
                #looking for single reflection if only one pattern was
                # entered
                if rv == pattern1 and not pattern2:
                    result += [(p, ref)]

                if not pattern2:
                    continue
                #or for concatenation of both were
                if rv[:len(pattern1)] == pattern1 and \
                   rv[-len(pattern2):] == pattern2:
                    result += [p, ref]

    return result


class hpp(AuditPlugin):
    """
    Identify client-side http parameter pollution vulnerabilities.
    """

    def __init__(self):
        AuditPlugin.__init__(self)
        self.parser = etree.HTMLParser(remove_blank_text=True, remove_comments=True)

    def audit(self, freq, orig_response):
        """
        Tests an URL for HPP vulnerabilities.
        :author: Dmitry Roshchin (nixwizard@gmail.com)
        """

        if not orig_response.is_text_or_html():
            return

        if not orig_response.get_code() == 200:
            return

        method = freq.get_method()

        if method == 'GET':
            qs = freq.get_querystring()

        precedence = None
        #finding reflected params if any
        for param in qs:
            value = qs[param][0]
            #checking if the value is number or string so that our
            #reflection test request would be more legitimate
            if value.isdigit():
                newval = unicode(int(value)+1)
            else:
                newval = REFLECT_TOKEN

            if precedence:
                continue

            mutants = create_mutants(freq, [newval],
                                     fuzzable_param_list=[param],
                                     mutant_tuple=(QSMutant,))
            mu = mutants[0]
            #doing reflection test for the param
            rtest_resp = self._uri_opener.send_mutant(mu)
            if not rtest_resp.get_code() == 200:
                #no need to seek reflection if it is not OK
                continue

            if orig_response.body == rtest_resp.body:
                #parameter param is not being reflected going for the next
                continue

            #Now we are doing precedence test
            u = str(mu.get_uri())
            #this hack is to make w3af send request with unencoded qs
            #because as long as we are trying to use qs it urlencodes the
            #second instance of param with new value
            ptest_url = URL(u.replace(newval,
                                      value + '&' + param + '=' + newval))
            ptest_resp = self._uri_opener.GET(ptest_url)
            ptest_resp_code = ptest_resp.get_code()

            if not ptest_resp_code == 200:
                om.out.debug(u"Precedence check request to the uri %s "
                             u"failed! "
                             u"Got response code %s in response id %s\n"
                             u"Unable to continue HPP detection. "
                             u"Resource might be protected by a WAF,"
                             % (ptest_url, ptest_resp_code, ptest_resp.id))
                #no need to continue with the param if it is not 200 OK
                continue

            ptest_body = ptest_resp.body

            if fuzzy_equal(orig_response.body,
                           ptest_body, EQUALITY_THRESHOLD):
                precedence = FIRST
                self.client_side(freq, orig_response, precedence, value, param)
                continue

            if fuzzy_equal(rtest_resp.body, ptest_body, EQUALITY_THRESHOLD):
                precedence = LAST
                self.client_side(freq, orig_response, precedence, value, param)
                continue

            concat = find_reflection(ptest_resp, None, [value, newval])

            if concat:
                desc = u'Concatenation of values of the two input parameters ' \
                       u'with the same name \"%s\" detected inside HTML ' \
                       u'code of response body.\nThe request url was %s.\n' \
                       u'Got concatenated output reflected in this link %s\n' \
                       u'This \"feature\" may be used in different WAF ' \
                       u'bypassing techniques.'
                desc = desc % (param, ptest_url, concat[1])

                i = Info(u'Input concatenation detected', desc, ptest_resp.id,
                         self.get_name())
                i.set_url(ptest_url)
                i.precedence = CONCAT
                self.kb_append(self, 'hpp', i)
                return

            om.out.debug(u'Unable to determine precedence for HPP detection '
                         u'with this request %s. Presumably not vulnerable to'
                         u' HPP.' % ptest_url)
            return

    def client_side(self, freq, orig_response, precedence, value, param):

        reflections = find_reflection(orig_response, precedence, [value])

        for reflection in reflections:
            #getting the list of exploitable params
            forgeable = get_forgeable(reflection, precedence)

            for f in forgeable:
                init_val = reflection[1].get_querystring()[f][0]
                if init_val.isdigit():
                    forged_val = str(int(init_val)+1)
                else:
                    forged_val = FORGE_TOKEN
                #building attack payload and exploiting
                payloads = [unicode(value) + '&' + f + '=' + forged_val]

                mutants = create_mutants(freq, payloads,
                                         fuzzable_param_list=param,
                                         mutant_tuple=(QSMutant,))
                mu = mutants[0]

                vtest_resp = self._uri_opener.send_mutant(mu)
                #checkig for successful exploitation
                r = find_reflection(vtest_resp, precedence, [forged_val])
                if r:
                    msg = u"The %s uri is vulnerable to HPP attack: value of " \
                          u"parameter %s can be forged using URL: %s, " \
                          u"precedence is %s"
                    msg = msg % (freq.get_uri(), r, mu.get_uri(), precedence)
                    v = Vuln.from_mutant(u'HPP', desc=msg, mutant=mu,
                                         plugin_name='hpp', response_ids=[],
                                         severity=severity.MEDIUM)
                    v.precedence = precedence
                    v.set_url(freq.get_uri())
                    # debug_msg = debug_msg % (rid, freq.get_uri())
                    self.kb_append_uniq(self, 'hpp', v,)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin detects client-side HTTP Parameter Pollution
        vulnerabilities using the following technique. First it detects if any
        of the input params is being reflected. If value of such parameter
        exists in any of the links of received HTML code it will try to forge
        it using HPP attack according to determined precedence or just
        report if precedence is concatenation.
        """
