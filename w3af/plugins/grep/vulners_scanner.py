"""
vulners_scanner.py

Copyright 2018 Vulners.com Team: Kir Ermakov (isox@vulners.com)

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

# w3af object imports here
import w3af.core.data.constants.severity as severity
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.quick_match.multi_re import MultiRE
from w3af.core.data.kb.vuln import Vuln
import w3af.core.controllers.output_manager as om
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import STRING
from w3af.core.data.options.option_list import OptionList

# Additional modules imports
import vulners
import collections
import re

class vulners_scanner(GrepPlugin):
    """
    Find software vulnerabilities using Vulners.com API

    Tests from the console mode:

    With API key:

    plugins grep vulners_scanner
    plugins grep config vulners_scanner
    set vulners_api_key YOUR_API_KEY_HERE
    back
    target set target VULNERABLE_WEBSITE
    start


    Without API key:

    plugins grep vulners_scanner
    target set target VULNERABLE_WEBSITE
    start

    :author: Vulners.com Team: Kir Ermakov (isox@vulners.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Vulners shared objects
        self._vulners_api = None
        self._vulners_api_key = None
        self.rules_table = None
        self.rules_updated = False

        self._already_visited = ScalableBloomFilter()
        self._vulnerability_cache = {}

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = ('Vulners API key for extended scanning rate limits.'
             'You can obtain one for free at https://vulners.com')
        o = opt_factory('vulners_api_key', self._vulners_api_key, d, STRING)
        ol.add(o)
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().
        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._vulners_api_key = options_list['vulners_api_key'].get_value()


    def update_vulners_rules(self):
        # Get fresh rules from Vulners.
        try:
            self.rules_table = self.get_vulners_api().rules()
            # Adapt it for MultiRe structure [(regex,alias)] removing regex duplicated
            regexAliases = collections.defaultdict(list)
            for softwareName in self.rules_table:
                regexAliases[self.rules_table[softwareName].get('regex')] += [softwareName]
            # Now create fast RE filter
            # Using re.IGNORECASE because w3af is modifying headers when making RAW dump. Why so? Raw must be raw!
            self._multi_re = MultiRE(((regex, regexAliases.get(regex)) for regex in regexAliases), re.IGNORECASE)
        except Exception as e:
            self.rules_table = None
            error_message = 'Vulners plugin failed to init with error: %s'
            om.out.error(error_message % e)

    def get_vulners_api(self):
        # Lazy import. Just not to make it in the __init__
        # Other way API will try to communicate Vulners right at the w3af startup
        if not self._vulners_api:
            # Don't forget to setup Vulners API key if you have one
            self._vulners_api = vulners.Vulners(api_key= self._vulners_api_key)
        return self._vulners_api

    def check_vulners(self, software_name, software_version, check_type):
        vulnerabilities = {}
        cached_result = self._vulnerability_cache.get((software_name, software_version, check_type))
        if cached_result:
            return cached_result
        # Ask Vulners about vulnerabilities
        if check_type == 'software':
            vulnerabilities = self.get_vulners_api().softwareVulnerabilities(software_name, software_version)
        elif check_type == 'cpe':
            cpe_string = "%s:%s" % (software_name, software_version)
            vulnerabilities = self.get_vulners_api().cpeVulnerabilities(cpe_string.encode())
        self._vulnerability_cache[(software_name, software_version, check_type)] = vulnerabilities
        return vulnerabilities

    def get_severity(self, cvss_score):
        # This table can be actually modified
        # That's only my opinions on the severity vs CVSS.score
        # Maybe move it to the options later?
        cvss_score = cvss_score * 10
        if cvss_score in range(20, 30):
            return severity.LOW
        elif cvss_score in range(30, 70):
            return severity.MEDIUM
        elif cvss_score in range(70, 100):
            return severity.HIGH
        else:
            return severity.INFORMATION

    def grep(self, request, response):
        """
        Plugin entry point, search for vulnerable software banners  in web application HTTP responses.
        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None

        """
        # Lazy update rules if it's first start of the plugin
        if not self.rules_updated:
            self.update_vulners_rules()
            self.rules_updated = True

        # Check if we have downloaded rules well.
        # If there is no rules - something went wrong, time to exit.
        if not self.rules_table:
            return
        # We do not parse non-text output
        if not response.is_text_or_html():
            return
        if response.get_url().get_domain_path() in self._already_visited:
            return

        self._already_visited.add(response.get_url().get_domain_path())

        raw_response = response.dump()

        # Here we will store uniq vulnerability map
        vulnerabilities_summary = {}

        for match, _, regex_comp, software_list in self._multi_re.query(raw_response):
            # If RE matched we have
            detected_version = match.group(1)
            for software_name in software_list:
                mathced_rule = self.rules_table[software_name]
                vulnerabilities_map = self.check_vulners(software_name= mathced_rule['alias'].encode(),
                                                         software_version= detected_version,
                                                         check_type= mathced_rule['type'].encode())
                flattened_vulnerability_list = [item for sublist in vulnerabilities_map.values() for item in sublist]
                for bulletin in flattened_vulnerability_list:
                    if bulletin['id'] not in vulnerabilities_summary:
                        vulnerabilities_summary[bulletin['id']] = bulletin

        # Now add KB's for found vulnerabilities
        for bulletin in vulnerabilities_summary.values():

            v = Vuln(name= bulletin['id'],
                     desc = bulletin['description'] or bulletin.get('sourceData', bulletin['title']),
                     severity = self.get_severity(bulletin.get('cvss', {}).get('score', 0)),
                     response_ids = response.id,
                     plugin_name = self.get_name())

            v.set_url(response.get_url())

            self.kb_append_uniq(location_a = self,
                                location_b = 'vulners',
                                info = v,
                                filter_by = 'URL')


    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every software banner and checks vulnerabilities online at vulners.com database.
        By default it's using anonymous Vulners API entry point. 
        If you will get 418 errors (rate limit fired) you can obtain API key for free at https://vulners.com.
        Then configure it at vulners_scanner as vulners_api_key variable.
        """
