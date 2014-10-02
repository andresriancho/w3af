#!/usr/bin/python
# -*- coding: utf-8
# vim: set fileencoding=utf-8

"""
fingerprint_WAF.py

Copyright 2014 Andres Riancho

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
import os
import json

from itertools import izip, repeat

from w3af import ROOT_PATH
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.kb.info import Info

UNKNOWN = 'Unknown'


class fingerprint_WAF(InfrastructurePlugin):
    """
    Identify if a Web Application Firewall is present and if possible identify
    the vendor and version.

    :Author: Achim Hoffmann )at( sicsec .dot. com
    """

    def __init__(self):
        """
        CHANGELOG:
        Sep/08/2014- Author Achim Hoffmann )at( sicsec .dot. com
        - redesign of former fingerprint_WAF.py by Andrés Riancho

        Currently (09/2014) most cookie names are matched case insensitive using
        python's re.IGNORECASE . This should be configurable.

        Feb/17/2009- Added Signatures by Aung Khant (aungkhant[at]yehg.net):
        - Old version F5 Traffic Shield, NetContinuum, TEROS, BinarySec
        """
        super(fingerprint_WAF, self).__init__()
        
        # Load WAF data
        self.waf_checks = file(os.path.join(ROOT_PATH, 'plugins', 'infrastructure',
                                       'fingerprint_waf',
                                       'waf_fingerprints.json'))
        
        waf_vendors = file(os.path.join(ROOT_PATH, 'plugins', 'infrastructure',
                                        'fingerprint_waf',
                                        'waf_vendors.json'))

        self.waf_checks = json.load(self.waf_checks)
        self.waf_vendors = json.load(waf_vendors)

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request):
        for waf_name, waf_check in self.waf_checks:
            max_score = 0
            score = 0

            status = waf_check['status']
            code = waf_check['code']
            description = waf_check['description']
            test_path = waf_check['test_path']
            content = waf_check['content']
            header = waf_check['header']

            om.out.debug('Performing %s detection...' % self.waf_vendors[waf_name])

            if waf_name not in self.waf_vendors:
                # inform programmer to properly adjust internal data
                msg = "Internal error in fingerprint_waf: '%s' not defined in"\
                      " vendors file"
                om.out.debug(msg % waf_name)
                self.waf_vendors[waf_name] = [UNKNOWN, UNKNOWN, UNKNOWN]

            # store matches, same as on entry in self.waf_checks{}
            waf_matches = ['' for _idx in range(0, WAF_MAXIDX)]

            # Send the request to the defined server and path
            url = fuzzable_request.get_url()
            test_url = url.url_join(test_path)
            response = self._uri_opener.GET(test_url, cache=True)

            # all following checks work like:
            #   if there is something to check (aka a pattern in _checks[])
            #      increment total score
            #      get corresponding data from request
            #      if regex matches data
            #          increment score

            _regex = _checks[WAF_STCODE]
            if not _regex == '':
                max_score += 1
                _data = response.get_code()
                if _data == _regex:
                    score += 1
                    waf_matches[WAF_STCODE] = _data

            _regex = _checks[WAF_STATUS]
            if not _regex == '':
                max_score += 1
                _data = response.get_statustext()
                if re.match(_regex, _data, re.IGNORECASE):
                    score += 1
                    waf_matches[WAF_STATUS] = _data

            _regex = _checks[WAF_PAGE]
            if not _regex == '':
                max_score += 1
                _data = response.get_body()
                #dbx print("# BODY { %s \n#}" % _data)
                if re.match(_regex, _data, flags=re.DOTALL|re.IGNORECASE):
                    score += 1
                    waf_matches[WAF_PAGE] = re.match(_regex, _data, flags=re.DOTALL|re.IGNORECASE).group(1) # using matched string instead of _data to avoid huge output

            _regex = _checks[WAF_HEADER]
            if not _regex == '':
                _header = re.split('\r?\n', response.get_header())
                for _idx in range(WAF_HEADER, len(_checks)):
                    max_score += 1
                    for _data in _header:
                        #dbx print("# HEAD { %s \n#}" % _data)
                        if re.match(_checks[_idx], _data, re.IGNORECASE):
                            score += 1
                            waf_matches[_idx] = _data

            if score > 0:
                prob = score * 100 / max_score
                text = "detected:\t%s; probability %s%% (with %s matches out of %s)" % (waf, prob, score, max_score)
            else:
                text = "skipped:\t" if max_score == 0 else "not detected:\t"
                text = text + waf
                om.out.debug(text)

            while _debug == 1:
                if re.match("^skipped", text): break
                msg = "#   %14s | %48s | %s"
                print("# matches for self.waf_checks['%s']:" % waf)
                print(msg % ('match type', 'REGEX pattern', 'matched string'))
                print(msg % ('--------------', '------------------------------------------------', '----------------'))
                for _idx in range(0, len(self.waf_checks[waf])):  # loop over smallest list to avoid "index out of range"!
                    if self.waf_checks_desc['WAF-ID'][_idx] == 'Description':
                        continue
                    msg_line = "%s" % self.waf_checks_desc['WAF-ID'][_idx]
                    print(msg % (msg_line, self.waf_checks[waf][_idx], waf_matches[_idx]))
                print(msg % ('--------------', '------------------------------------------------', '----------------'))
                break

            print(text)
            
    def _report_finding(self, name, response, protected_by=None):
        """
        Creates a information object based on the name and the response
        parameter and saves the data in the kb.

        :param name: The name of the WAF
        :param response: The HTTP response object that was used to identify the WAF
        :param protected_by: A more detailed description/version of the WAF
        """
        desc = 'The remote network seems to have a "%s" WAF deployed to' \
               ' protect access to the web server.'
        desc = desc % name

        if protected_by:
            desc += ' The following is the WAF\'s version: "%s".' % protected_by

        i = Info('Web Application Firewall fingerprint', desc, response.id,
                 self.get_name())
        i.set_url(response.get_url())
        i.set_id(response.id)

        kb.kb.append(self, name, i)
        om.out.information(i.get_desc())

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['infrastructure.afd']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Try to fingerprint the Web Application Firewall that is running on the
        remote end.

        Please note that the detection of the WAF is performed by the
        infrastructure.afd plugin (afd stands for Active Filter Detection).
        """
