"""
vulners.py

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
import re
import json
import collections

import vulners

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.quick_match.multi_re import MultiRE
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import STRING
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.misc.cvss import cvss_to_severity


class vulners_db(GrepPlugin):
    """
    Find software vulnerabilities using Vulners.com API

    Tests from the console mode:

    With API key:

        plugins grep vulners
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

        # Vulners rules JSON url
        self._vulners_rules_url = URL('https://raw.githubusercontent.com/vulnersCom/detect-rules/master/rules.json')

        # Vulners shared objects
        self._vulners_api = None
        self._vulners_api_key = ''
        self.rules_table = None
        self.rules_updated = False

        self._already_visited = ScalableBloomFilter()
        self._vulnerability_cache = {}
        self._multi_re = None

    def grep(self, request, response):
        """
        Plugin entry point, search for vulnerable software banners in web
        application HTTP responses.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None

        """
        # Lock and init rules and API wrapper
        with self._plugin_lock:
            if not self.rules_updated:
                # Updating rules
                self.update_vulners_rules()
                self.rules_updated = True

                # Trying to init Vulners API
                self.setup_vulners_api()

        # Check if we have downloaded rules well.
        # If there is no rules - something went wrong, time to exit.
        # If there is no API instance - same story. We cant go further.
        if not self.rules_table or not self._vulners_api:
            return

        # We do not parse non-text output
        if not response.is_text_or_html():
            return

        if response.get_url().get_domain_path() in self._already_visited:
            return

        self._already_visited.add(response.get_url().get_domain_path())

        raw_response = response.dump()

        # Here we will store unique vulnerability map
        vulnerabilities_summary = {}

        for match, _, regex_comp, software_list in self._multi_re.query(raw_response):
            detected_version = match.group(1)

            for software_name in software_list:
                matched_rule = self.rules_table[software_name]

                vulnerabilities_map = self.check_vulners(software_name=matched_rule['alias'].encode(),
                                                         software_version=detected_version,
                                                         check_type=matched_rule['type'].encode())

                flattened_vulnerability_list = [item for sublist in vulnerabilities_map.values() for item in sublist]
                for bulletin in flattened_vulnerability_list:
                    if bulletin['id'] not in vulnerabilities_summary:
                        vulnerabilities_summary[bulletin['id']] = bulletin

        # Now add KB's for found vulnerabilities
        for bulletin in vulnerabilities_summary.values():

            v = Vuln(name=bulletin['id'],
                     desc=bulletin['description'] or bulletin.get('sourceData', bulletin['title']),
                     severity=cvss_to_severity(bulletin.get('cvss', {}).get('score', 0)),
                     response_ids=response.id,
                     plugin_name=self.get_name())

            v.set_url(response.get_url())

            v[VulnerableSoftwareInfoSet.ITAG] = bulletin['id']

            self.kb_append_uniq_group(location_a=self,
                                      location_b='HTML',
                                      info=v,
                                      group_klass=VulnerableSoftwareInfoSet)

    def update_vulners_rules(self):
        """
        Get fresh rules from Vulners Github. The rules are regular expressions
        which are used to extract information from the HTTP response.

        Rules can be found at vulners github repository. They were not included
        into the w3af repository because of licensing incompatibilities.

        Paranoid? Check gitlog and regexes.
        """
        # w3af grep plugins shouldn't (by definition) perform HTTP requests
        # But in this case we're breaking that general rule to retrieve the
        # DB at the beginning of the scan
        try:
            http_response = self._uri_opener.GET(self._vulners_rules_url,
                                                 binary_response=True,
                                                 respect_size_limit=False)
        except Exception as e:
            msg = 'Failed to download Vulners regex rules table: "%s"'
            om.out.error(msg % e)
            return

        if http_response.get_code() != 200:
            msg = ('Failed to download the Vulners regex rules table, unexpected'
                   ' HTTP response code %s')
            om.out.error(msg % http_response.get_code())
            return

        json_table = http_response.get_raw_body()
        self.rules_table = json.loads(json_table)

        # Adapt it for MultiRe structure [(regex,alias)] removing regex duplicated
        regex_aliases = collections.defaultdict(list)
        for software_name in self.rules_table:
            regex_aliases[self.rules_table[software_name].get('regex')] += [software_name]

        # Now create fast RE filter
        # Using re.IGNORECASE because w3af is modifying headers when making RAW dump.
        # Why so? Raw must be raw!
        self._multi_re = MultiRE(((regex, regex_aliases.get(regex)) for regex in regex_aliases),
                                 re.IGNORECASE)

    def setup_vulners_api(self):
        try:
            self._vulners_api = vulners.Vulners(api_key=self._vulners_api_key or None)
        except Exception as e:
            # If API key is wrong or API key is not a string it will raise exception
            msg = 'Failed to initialize Vulners API: "%s"'
            om.out.error(msg % e)
            return

    def check_vulners(self, software_name, software_version, check_type):
        if not software_name:
            return {}

        if not software_version:
            return {}

        cached_result = self._vulnerability_cache.get((software_name, software_version, check_type))
        if cached_result:
            return cached_result

        args = (software_name, software_version, check_type)
        om.out.debug('Detected %s version %s (check type: %s)' % args)

        vulnerabilities = {}

        # Ask Vulners about vulnerabilities
        #
        # We will do it in try-except mode to work properly with potential network
        # connectivity problem or in case Vulners is down.
        try:
            if check_type == 'software':
                vulnerabilities = self._vulners_api.softwareVulnerabilities(software_name, software_version)
            elif check_type == 'cpe':
                cpe_string = "%s:%s" % (software_name, software_version)
                vulnerabilities = self._vulners_api.cpeVulnerabilities(cpe_string.encode())
        except Exception as e:
            msg = 'Failed to make Vulners API request: "%s"'
            om.out.error(msg % e)
            # Return empty dict not to stop here.
            # Maybe next time API will answer correctly.
            return {}

        # If call was OK cache the data and return results
        self._vulnerability_cache[(software_name, software_version, check_type)] = vulnerabilities
        return vulnerabilities

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = ('Vulners API key for extended scanning rate limits.'
             ' Obtain an API key for free at https://vulners.com/')
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

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin extracts software banners and checks vulnerabilities online
        at vulners.com database.
        
        By default the grep plugin uses anonymous Vulners API entry point
        (rate-limited to ~10 rps), it is possible to get a free API key at
        https://vulners.com/ to avoid rate limits.
        
        Configure the API key using the vulners_api_key user-configured
        parameter.
        """


class VulnerableSoftwareInfoSet(InfoSet):
    ITAG = 'vulnerability_id'
    TEMPLATE = (
        'Vulners plugin detected software with known vulnerabilities.'
        ' The identified vulnerability is "{{ name }}".\n'
        '\n'
        ' The first ten URLs where vulnerable software was detected are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
