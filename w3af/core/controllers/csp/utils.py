"""
utils.py

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
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
"""
import re
from urlparse import urlparse
from mimetypes import MimeTypes
from collections import namedtuple
import w3af.core.data.constants.severity as severity
from w3af.core.controllers.exceptions import BaseFrameworkException
import w3af.core.data.parsers.parser_cache as parser_cache

# Valid Mime Types list
MIME_TYPES = MimeTypes().types_map[1].values()

# Define NamedTuple tuple subclass to represents a CSP vulnerability.
# Declare type here in order to expose it with project visibility
# and permit cPickle processing to see it. See link below:
# http://stackoverflow.com/questions/4677012/python-cant-pickle-type-x-attribute-lookup-failed
CSPVulnerability = namedtuple('CSPVulnerability',
                              ['desc', 'severity', 'type', 'directive'])


class CSPDirective(object):
    """
    Represents CSP directive.
    """
    name = "CSPDirective"
    value = ""
    source_list = []
    _source_limit = None
    trusted_hosts = []
    syntax_errors = []

    vuln_wildcard_tpl = "Directive '%s' allows all sources."
    vuln_inline_tpl = "Directive '%s' allows 'unsafe-inline'. Use nonces or hashes."
    vuln_eval_tpl = """Directive '%s' contains risky 'unsafe-eval' keyword source 
or equivalent like blob: or filesystem:. Found: %s."""
    vuln_untrust_tpl = "Directive '%s' contains untrusted sources: %s."
    vuln_source_limit_tpl = "Directive '%s' contains too many sources in source list."
    vuln_data_source_tpl = """Directive '%s' contains 'data:' in source list. 
Allowing 'data:' URLs is equivalent to 'unsafe-inline'."""
    vuln_parse_source_tpl = """CSP policy parsing error. 
The source list for directive '%s' contains an invalid source: %s."""

    def __init__(self, name=None):
        if name:
            self.name = name
   
    @property
    def source_limit(self):
        return self._source_limit

    @source_limit.setter
    def source_limit(self, value):
        self._source_limit = value

    def init_value(self, directive_value):
        """
        Init value of directive.

        :param directive_value: string value of directive
        :return: True if initialization was success, otherwise False
        """
        directive_value = directive_value.strip()
        if not self._parse_source_list(directive_value):
            return False
        self.value = directive_value
        return True

    def _normalize_host_source(self, token):
        """
        Normalize host source for furher processing.

        :param token: string token of source
        :return: normalized host source value
        """
        result = token
        o = urlparse(result)
        # scheme-part
        if not o.scheme:
            result = '//' + result
        # port-part
        result = result.replace(":*", ":0")
        # host-part
        result = result.replace("*.", "Q.")
        result = result.replace("*", "A")
        return result

    def _is_host_source(self, token):
        """
        Check if token is host-source.

        :param token: string token of source
        :return: boolean result
        """
        if token.startswith("'"):
            return False
        tmp = self._normalize_host_source(token)
        o = urlparse(tmp)
        if re.search("[^a-zA-Z:*0-9.-]", o.netloc):
            return False
        if not o.hostname:
            return False
        if o.geturl() == tmp:
            return True

    def _is_valid_source(self, token):
        """
        Check if token is valid source.
        See also https://www.w3.org/TR/CSP/#source-list-syntax

        :param token: string token of source
        :return: boolean result
        """
        if token == "*":
            return True
        # keyword-source
        if token in ["'self'", "'unsafe-inline'", "'unsafe-eval'"]:
            return True
        # nonce-source
        p = re.compile("'nonce-[a-zA-Z0-9+/]+[=]{0,2}'")
        if p.match(token):
            return True
        # hash-source
        p = re.compile("'(sha256|sha384|sha512)-[a-zA-Z0-9+/]+[=]{0,2}'")
        if p.match(token):
            return True
        # scheme-source
        tmp = self._normalize_host_source(token)
        o = urlparse(tmp)
        if o.scheme + ':' == tmp:
            return True
        # host-source
        if self._is_host_source(token):
            return True
        return False

    def _parse_source_list(self, directive_value):
        """
        Parse directive value and set up directive sourse list.
        See also https://www.w3.org/TR/CSP/#source-list-parsing

        :param directive_value: string directive value
        :return: True if source list was successfully parsed
        """
        self.syntax_errors = []
        source_list = directive_value.strip()
        if source_list.lower() == "'none'":
            self.source_list = []
            return True
        result = []
        for token in source_list.split(" "):
            if self._is_valid_source(token):
                result.append(token)
            else:
                self.syntax_errors.append(
                    CSPVulnerability(self.vuln_parse_source_tpl % (self.name, token),
                    severity.HIGH, 'syntax', ''))
        self.source_list = result
        return True

    def get_nonces_hashes(self, nonces=True, hashes=True):
        """
        Find nonces and hashes in source list.

        :return: list of hashes and nonces
        """
        result = []
        targets = []

        if nonces:
            targets.append("'nonce-")

        if hashes:
            targets.extend(["'sha256-", "'sha384-", "'sha512-"])

        for source_expression in self.source_list:
            for s in targets:
                if source_expression.startswith(s):
                    result.append(source_expression)
        return result

    def _find_wildcard_vulns(self, severity):
        """
        Find wildcard vulnerabilities.

        :param severity: Severity for results
        :return: list of vulnerabilities
        """
        vulns = []
        if "*" in self.source_list:
            vuln = CSPVulnerability(self.vuln_wildcard_tpl % self.name,
                                    severity, 'wildcard', self.name)
            vulns = [vuln]
        return vulns

    def _check_data_source(self):
        """
        Check if data: is included in source list of risky directives

        :return: list of vulnerabilities
        """
        vulns = []
        if 'data:' in self.source_list \
                and self.name in ['default-src', 'script-src', 'object-src']:
            vuln = CSPVulnerability(self.vuln_data_source_tpl % self.name,
                severity.HIGH, 'data_source', self.name)
            vulns = [vuln]
        return vulns

    def _find_eval_vulns(self):
        """
        Check if 'unsafe-eval' or equivalent is included in source list of directive.

        :return: list of vulnerabilities
        """
        if not self.report_eval:
            return []

        vulns = []
        result = filter(lambda x: x == "'unsafe-eval'", self.source_list)
        # See "Security Considerations for GUID URL schemes"
        # https://www.w3.org/TR/CSP/#source-list-guid-matching
        risky_schemes = filter(lambda x: x in ['blob:', 'filesystem:'],
            self.source_list)

        if self.name in ['default-src', 'script-src'] and risky_schemes:
            result.extend(risky_schemes)
       
        if result:
            vulns.append(CSPVulnerability(
                self.vuln_eval_tpl % (self.name, ', '.join(result)),
                severity.MEDIUM, 'eval', self.name))
        return vulns

    def _check_source_limit(self):
        """
        Find source limit exceed vulnerabilities
        (when too many sources in directive source list).

        :return: list of vulnerabilities
        """
        vulns = []
        if not self.source_limit:
            return []
        if len(self.source_list) > self.source_limit:
            vuln = CSPVulnerability(self.vuln_source_limit_tpl % self.name,
                severity.LOW, 'source_limit', self.name)
            vulns = [vuln]
        return vulns

    def _check_untrusted_sources(self):
        """
        Find untrusted hosts in source list.

        :return: list of vulnerabilities
        """
        untrusted = []
        vulns = []
        if not self.trusted_hosts:
            return []

        for source in self.source_list:
            if self._is_host_source(source):
                tmp = self._normalize_host_source(source)
                o = urlparse(tmp)
                for t_host in self.trusted_hosts:
                    if o.hostname.endswith(t_host):
                        break
                else:
                    untrusted.append(source)
      
        if untrusted:
            vuln = CSPVulnerability(self.vuln_untrust_tpl % (self.name, ", ".join(untrusted)),
                severity.LOW, 'untrust', self.name)
            vulns = [vuln]
        return vulns

    def _find_vulns(self):
        """
        Find all vulnerabilities in child directive.

        :return: list of vulnerabilities
        """
        return []

    def find_vulns(self):
        """
        Find all vulnerabilities in directive.

        :return: list of vulnerabilities
        """
        # TODO
        # 1. Check for random value in nonce
        # https://www.w3.org/TR/CSP/#source-list-guid-matching
        #
        vulns = []
        vulns.extend(self._find_wildcard_vulns(severity.MEDIUM))
        vulns.extend(self._check_source_limit())
        vulns.extend(self._check_untrusted_sources())
        vulns.extend(self._check_data_source())
        vulns.extend(self._find_eval_vulns())
        vulns.extend(self._find_vulns())

        if self.unsafe_inline_enabled() and not self.get_nonces_hashes():
            vuln = CSPVulnerability(self.vuln_inline_tpl % self.name, 
                severity.HIGH, 'inline', self.name)
            vulns.append(vuln)
        return vulns + self.syntax_errors

    def __str__(self):
        return self.name + " " + self.value

    def __eq__(self, other):
        return self.name.upper() == other.name.upper()

    def unsafe_inline_enabled(self):
        """
        Check if there is 'unsafe-inline' keyword in source list.

        :return: True if there is 'unsafe-inline' in source list
        """
        return "'unsafe-inline'" in self.source_list


class DefaultSrcDirective(CSPDirective):
    """
    Represents CSP 'default-src' directive.
    """
    name = "default-src"
    strictness = 0
    vuln_strictness_tpl = "Level of strictness for directive 'default-src' permits only value %s."

    @CSPDirective.source_limit.setter
    def source_limit(self, value):
        """
        Set smaller value because of risky nature of the directive.

        :param value: new value for directive
        """
        value = value if not value else int(value/2)
        self._source_limit = value

    def _find_vulns(self):
        """
        Find all issues because of strictness level for default-src.

        :return: list of vulnerabilities
        """
        if not self.strictness:
            return []

        vulns = []
        strictness_levels = [(1, "'self'"), (2, "'none'")]

        for strictness, value in strictness_levels:
            if self.strictness == strictness \
                    and (len(self.source_list) > 1 or self.source_list[0] != value):
                vuln = CSPVulnerability(self.vuln_strictness_tpl % value, severity.MEDIUM,
                    'default_src_strictness', self.name)
                vulns.append(vuln)

        return vulns


class ScriptSrcDirective(CSPDirective):
    """
    Represents CSP 'script-src' directive.
    """
    name = "script-src"

    @CSPDirective.source_limit.setter
    def source_limit(self, value):
        """
        Set smaller value because of risky nature of the directive.

        :param value: new value for directive
        """
        value = value if not value else int(value/2)
        self._source_limit = value


class SandboxDirective(CSPDirective):
    """
    Represents CSP 'sandbox' directive.
    """
    name = "sandbox"
    flags = []

    def init_value(self, directive_value):
        """
        Init value of directive.

        :param directive_value: string value of directive
        :return: True if initialization was success, otherwise False
        """
        self.value = directive_value
        self.flags = self._parse_flag_list(directive_value)
        return True

    def _valid_flag(self, flag):
        """
        Check if flag is valid

        :return: True if flag is valid
        """
        valid_flags = ['allow-forms', 'allow-pointer-lock',
            'allow-popups', 'allow-same-origin',
            'allow-scripts', 'allow-top-navigation']

        if flag in valid_flags:
            return True
        else:
            return False

    def _parse_flag_list(self, directive_value):
        """
        Parse flag list for sandbox directive.

        :param directive_value: value of directive
        :return: list of flags
        """
        flag_list = directive_value.strip()
        result = []
        for flag in flag_list.split(" "):
            if self._valid_flag(flag):
                result.append(flag)
        return result


class PluginTypesDirective(CSPDirective):
    """
    Represents CSP 'plugin-types' directive.
    """
    # https://www.w3.org/TR/CSP/#media-type-list-syntax
    name = "plugin-types"
    media_type_list = []

    def init_value(self, directive_value):
        """
        Init value of directive.

        :param directive_value: string value of directive
        :return: True if initialization was success, otherwise False
        """
        directive_value = directive_value.strip()
        if not directive_value:
            return False
        self.value = directive_value
        self.media_type_list = self._parse_media_type_list(directive_value)
        return True

    def _valid_media_type(self, media_type):
        """
        Check if media type is valid.

        :param media_type: media type
        :return: True if is valid
        """
        if media_type.lower() not in MIME_TYPES:
            return False
        return True

    def _parse_media_type_list(self, directive_value):
        """
        Parse media type list.
        See also https://www.w3.org/TR/CSP/#media-type-list-parsing
       
        :param directive_value: directive value
        :return: list of media types
        """
        media_type_list = directive_value.strip()
        result = []
        for media_type in media_type_list.split(" "):
            if self._valid_media_type(media_type):
                result.append(media_type)
        return result


class CSPPolicy(object):
    """
    Represents policy from Content Security Policy Level 2
    https://www.w3.org/TR/CSP/
    """
    version = 2
    report_only = False
    directives = []
    syntax_errors = []
    value = ""
    trusted_hosts = []
    report_no_report_uri = False
    report_eval = True
    source_limit = None
    default_src_strictness = 0
    report_not_fallback = False
    vuln_parse_directive_tpl = "CSP policy parsing error. Unrecognized directive '%s'."
    vuln_no_report_uri_tpl = "The CSP policy doesn't contain 'report-uri' directive."
    vuln_required_tpl = """Directive '%s' is not defined. NB! It does not fall back 
to the default sources when the directive is not defined."""
    vuln_default_tpl = """Directive 'default-src' is not defined. If a 'default-src' directive 
is not explicitly specified, wildcard ('*') becomes default sources."""

    def get_header_name(self, report_only=False):
        """
        :param report_only: flag for result
        :return: CSP header name
        """
        header_name = "Content-Security-Policy"
        if self.report_only or report_only:
            header_name += "-Report-Only"
        return header_name

    def pretty(self):
        """
        :return: pretty string representation of CSP policy
        """
        return (self.get_header_name() + ":\n    "
                + ";\n    ".join([str(d) for d in self.directives]))

    def __str__(self):
        return self.get_header_name() + ": " + self.value

    def init_value(self, csp_value, banned_directives=[]):
        """
        Init value of the policy.

        :param csp_value: string value of policy
        :param banned_directives: list of banned directives (see meta tag)
        :return: True if initialization was success, otherwise False 
        """
        string_policy = csp_value.strip()
        if not string_policy:
            return False
        if self._parse_policy(string_policy, banned_directives):
            self.value = csp_value
            return True
        else:
            return False

    def init_from_header(self, header_name, header_value):
        """
        Init policy from CSP header.

        :param header_name: CSP header name
        :param header_value: CSP header value
        :return: True if initialization was success
        """
        string_policy = ""

        if header_name.upper().strip() == self.get_header_name().upper():
            string_policy = header_value.strip()
        elif header_name.upper().strip() == self.get_header_name(True).upper():
            self.report_only = True
            string_policy = header_value.strip()
        return self.init_value(string_policy)

    def make_directive(self, directive_name):
        """
        Make directive instance (factory method).

        :param directive_name: directive name for new directive
        :return: directive instance
        """
        simple_directives = [
            "object-src", "img-src", "media-src",
            "frame-src", "font-src", "connect-src", 
            "report-uri", "base-uri", "child-src", 
            "style-src", "form-action", "frame-ancestors",
            ]
        directive = None
        dname = directive_name.lower()
        if dname in simple_directives:
            directive = CSPDirective(dname)
        elif "default-src" == dname:
            directive = DefaultSrcDirective()
            directive.strictness = self.default_src_strictness
        elif "script-src" == dname:
            directive = ScriptSrcDirective()
        elif "sandbox" == dname:
            directive = SandboxDirective()
        elif "plugin-types" == dname:
            directive = PluginTypesDirective()
       
        if directive:
            directive.source_limit = self.source_limit
            directive.trusted_hosts = self.trusted_hosts
            directive.report_eval = self.report_eval
            return directive
        else:
            return None

    def _parse_policy(self, string_policy, banned_directives=[]):
        """
        Parse CSP policy and set list of directives.
        See also https://www.w3.org/TR/CSP/#policy-parsing

        :param string_policy: string value of policy
        :param banned_directives: list of banned directives (see meta tag)
        :return: True on success parsing
        """
        self.syntax_errors = []
        result = []
        tokens = [d.strip() for d in string_policy.strip().split(";")]
        tokens = filter(lambda x: x.strip(), tokens)

        for t in tokens:
            directive_name = t
            directive_value = ""
            i = t.find(" ")

            if i != -1:
                directive_name = t[:i]
                directive_value = t[i+1:]

            if directive_name in banned_directives:
                continue
           
            directive = self.make_directive(directive_name)
            # CSP syntax error
            if not directive:
                self.syntax_errors.append(
                        CSPVulnerability(self.vuln_parse_directive_tpl % directive_name,
                                         severity.HIGH, 'syntax', ''))
                continue
            if directive not in result:
                if directive.init_value(directive_value):
                    result.append(directive)
        if result:
            self.directives = result
            return True
        else:
            return False

    def get_directive_by_name(self, directive_name):
        """
        Get directive by name.

        :param directive_name: name of directive
        :return: directive if it exists in the policy, otherwise None
        """
        for d in self.directives:
            if d.name.lower() == directive_name.lower():
                return d
        return None

    def find_vulns(self):
        """
        Find all vulnerabilities in all directives.

        :return: result list of vulnerabilities
        """
        vulns = []
        for d in self.directives:
            d_vulns = d.find_vulns()
            if d_vulns:
                vulns.extend(d_vulns)
        # Check if report-uri exists
        if self.report_no_report_uri and not self.get_report_uri():
            vulns.append(CSPVulnerability(self.vuln_no_report_uri_tpl,
                         severity.LOW, 'reporting', ''))
        # Check directives which does not fall back to the default sources
        if self.report_not_fallback:
            for d in ['frame-ancestors', 'form-action', 'base-uri']:
                if not self.get_directive_by_name(d):
                    vuln = CSPVulnerability(self.vuln_required_tpl % d, severity.MEDIUM,
                                            'required', d)
                    vulns.append(vuln)
        # Check default-src
        if not self.get_directive_by_name('default-src'):
            vuln = CSPVulnerability(self.vuln_default_tpl, severity.MEDIUM,
                                    'default_required', 'default-src')
            vulns.append(vuln)
        return vulns + self.syntax_errors
   
    def find_vulns_by_directive(self, directive_name):
        """
        Find all vulnerabilities filtered by directive.

        :param directive_name: directive name
        :return: list of vulnerabilities
        """
        result = []
        for v in self.find_vulns():
            if v.directive == directive_name:
                result.append(v)
        return result

    def get_report_uri(self):
        """
        Get report uri if it exists.

        :return: report uri, otherwise None
        """
        report_uri = self.get_directive_by_name('report-uri')
       
        if report_uri:
            return report_uri.value
        else:
            return None

    def protects_against_xss(self):
        """
        Check if policy protects against XSS.
        See also https://www.w3.org/TR/CSP/#directives
       
        :return: True if protects, otherwise False
        """
        if not self.directives or self.report_only:
            return False

        risky_directives = []
        for dn in ['script-src', 'object-src', 'script-src']:
            risky_directives.append(self.get_directive_by_name(dn))
        default_src = self.get_directive_by_name('default-src')

        # must be enabled default_src or **all** risky directives
        if not (default_src or
                reduce(lambda x, y: x and y, risky_directives)):
            return False

        for rd in risky_directives:
            d = rd if rd else default_src
            for vuln in d.find_vulns():
                if vuln.severity == severity.HIGH:
                    return False
        return True

    def unsafe_inline_enabled(self):
        """
        Check if there is 'unsafe-inline' keyword in source list of
        script-src and style-src directives.

        :return: True if there is 'unsafe-inline' in source list of risky directives
        """
        for directive_name in ['script-src', 'style-src']:
            directive = self.get_directive_by_name(directive_name)
            if directive and directive.unsafe_inline_enabled():
                return True
        return False

    def get_nonces(self):
        """
        Find nonces in source list of directives.

        :return: list of nonces
        """
        result = []
        for d in self.directives:
            result.extend(d.get_nonces_hashes(nonces=True, hashes=False))
        return result
 

class CSP(object):
    """Content Security Policy Level 2
    https://www.w3.org/TR/CSP/"""
    policies = []
    response_id = None
    response_url = None
    trusted_hosts = []
    source_limit = None
    report_eval = True
    report_no_report_uri = False
    default_src_strictness = 0
    report_not_fallback = False

    def header_provides_csp(self, header_name):
        """
        Indicate if header is CSP header.

        :param header_name: name of the header
        :return: True if so, otherwise False
        """
        csp = CSPPolicy()
        header = header_name.upper().strip()
        if header == csp.get_header_name().upper() \
                or header == csp.get_header_name(True).upper():
            return True
        return False

    def _get_policies_from_meta(self, response):
        """
        Retrieve policy from meta tag.
        See also https://www.w3.org/TR/CSP/#delivery-html-meta-element
       
        :param response: HTTP response
        :return: list of policies
        """
        result = []

        if not response.is_text_or_html():
            return result

        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            return result

        meta_tag_list = dp.get_meta_tags()
        meta_values = []
        for tag in meta_tag_list:
            if tag.get('http-equiv', '') == "Content-Security-Policy":
                content = tag.get('content', '')
                if content:
                    meta_values.append(content)
        banned = ['report-uri', 'frame-ancestors', 'sandbox']
        for csp_value in meta_values:
            csp = CSPPolicy()
            csp.source_limit = self.source_limit
            csp.trusted_hosts = self.trusted_hosts
            csp.report_eval = self.report_eval
            csp.report_no_report_uri = self.report_no_report_uri
            csp.default_src_strictness = self.default_src_strictness
            csp.report_not_fallback = self.report_not_fallback
            if csp.init_value(csp_value, banned_directives=banned):
                result.append(csp)
        
        return result

    def init_from_response(self, response):
        """
        Init CSP policies from HTTP response.

        :param response: HTTP response
        :return: list of policies
        """
        # TODO
        # Merge multiple policies
        # https://www.w3.org/TR/CSP/#enforcing-multiple-policies
        self.policies = []
        # From headers
        headers = response.get_headers()
        for header_name in headers:
            if self.header_provides_csp(header_name):
                csp = CSPPolicy()
                csp.source_limit = self.source_limit
                csp.trusted_hosts = self.trusted_hosts
                csp.report_eval = self.report_eval
                csp.report_no_report_uri = self.report_no_report_uri
                csp.default_src_strictness = self.default_src_strictness
                csp.report_not_fallback = self.report_not_fallback
                if csp.init_from_header(header_name, headers[header_name]):
                    self.policies.append(csp)
        # From meta tag
        self.policies.extend(self._get_policies_from_meta(response))
        if self.policies:
            self.response_id = response.id
            self.response_url = response.get_url().uri2url()
            return len(self.policies)
        else:
            return False

    def protects_against_xss(self):
        """
        Check if policies protect against XSS.
        See also https://www.w3.org/TR/CSP/#directives
       
        :return: True if at least one of policies protects, otherwise False
        """
        for policy in self.policies:
            if policy.protects_against_xss():
                return True
        return False

    def __str__(self):
        return '|'.join([p.value for p in self.policies])

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def get_nonces(self):
        """
        Find nonces in source list of all directives in all policies.

        :return: set of nonces
        """
        result = set()
        for policy in self.policies:
            for nonce in policy.get_nonces():
                result.add(nonce)
        return result

    def find_nonce_vulns(self, csps):
        """
        Find cases when nonces in source list of CSP
        policy directives are not random in responses.

        :return: list of vulns
        """
        vulns = []
        filtered_csps = filter(lambda x: x.get_nonces(), csps)

        if self.get_nonces():
            filtered_csps.insert(0, self)

        if len(filtered_csps) < 2:
            return []

        prev = filtered_csps[0]
        for csp in filtered_csps[1:]:
            for policy in csp.policies:
                tmp = policy.get_nonces()
                if not tmp:
                    continue
                nonces = set(prev.get_nonces()).intersection(set(tmp))
                # Get intersection between nonces of policies!
                if nonces:
                    vulns.append(CSPVulnerability(
                        self.vuln_nonce_intersection_tpl % ", ".join(nonces),
                        severity.HIGH, 'nonce_intersection', ''))
                    return vulns
            prev = policy
        return vulns

    vuln_nonce_intersection_tpl = """There is intersection between nonces of at least two policies from different responses.
It means that nonce value is not random for every responose. Not random nonces: %s"""
