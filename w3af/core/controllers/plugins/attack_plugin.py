"""
AttackPlugin.py

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
import copy

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.controllers.misc.common_attack_methods import CommonAttackMethods
from w3af.core.controllers.exceptions import (NoVulnerabilityFoundException,
                                              ExploitFailedException,
                                              HTTPRequestException,
                                              ScanMustStopException,
                                              ScanMustStopByUnknownReasonExc,
                                              ScanMustStopByUserRequest)


class AttackPlugin(Plugin, CommonAttackMethods):
    """
    This is the base class for attack plugins, all attack plugins should inherit
    from it and implement the following methods :
        * _generate_shell
        * get_kb_location
        * get_attack_type
        * get_root_probability

    :author: Andres Riancho ((andres.riancho@gmail.com))
    """

    def __init__(self):
        Plugin.__init__(self)
        CommonAttackMethods.__init__(self)

        self._uri_opener = None
        self._footer = None
        self._header = None

        # User configured parameter
        self._generate_only_one = False

    def _generate_shell(self, vuln):
        """
        :param vuln: The vulnerability object to exploit.
        """
        msg = 'Plugin is not implementing required method _generate_shell'
        raise NotImplementedError(msg)

    def get_exploitable_vulns(self):
        vulns = []
        
        for location in self.get_kb_location():
            vulns.extend(kb.kb.get(location, location))
        
        return vulns

    def can_exploit(self, vuln_to_exploit=None):
        """
        Determines if audit plugins found exploitable vulns.

        :param vuln_to_exploit: The vulnerability id to exploit
        :return: True if we can exploit a vuln stored in the kb.
        """
        if vuln_to_exploit is not None:
            error_msg = 'can_exploit requires an integer list got %s instead.'
            if not isinstance(vuln_to_exploit, list):
                raise TypeError(error_msg % type(vuln_to_exploit))
            
            if not all([isinstance(_id, int) for _id in vuln_to_exploit]):
                raise TypeError(error_msg % type(vuln_to_exploit))
        
        vulns = self.get_exploitable_vulns()
        if vuln_to_exploit is not None:
            vulns = [v for v in vulns if v.get_id() == vuln_to_exploit]
            return bool(vulns)
        else:
            # The user didn't specified what vuln to exploit... so...
            return bool(vulns)

    def get_attack_type(self):
        """
        :return: The type of exploit, SHELL, PROXY, etc.
        """
        msg = 'Plugin is not implementing required method get_attack_type'
        raise NotImplementedError(msg)

    def GET2POST(self, vuln):
        """
        This method changes a vulnerability mutant, so all the data that was
        sent in the query string, is now sent in the postData; of course, the
        HTTP method is also changed from GET to POST.
        """
        vuln_copy = copy.deepcopy(vuln)
        mutant = vuln_copy.get_mutant()

        #    Sometimes there is no mutant (php_sca).
        if mutant is None:
            return vuln_copy

        if mutant.get_method() == 'POST':
            # No need to work !
            return vuln_copy

        else:
            # Need to create a new PostDataMutant, to be able to easily change
            # the values which we want to send in the HTTP post-data
            fre = FuzzableRequest(mutant.get_url(),
                                  headers=mutant.get_headers(),
                                  method='POST',
                                  cookie=mutant.get_cookie(),
                                  post_data=mutant.get_uri().querystring)
            pdm = PostDataMutant(fre)
            vuln_copy.set_mutant(pdm)

            return vuln_copy

    def get_root_probability(self):
        """
        :return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        """
        msg = 'Plugin is not implementing required method get_root_probability'
        raise NotImplementedError(msg)

    def get_type(self):
        return 'attack'

    def get_kb_location(self):
        """
        This method should return the vulnerability names (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds a
        vuln, and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding
        (attack.os_commanding) should return ['os_commanding',] in this method.
        
        If there is more than one location the implementation should return
        ['a', 'b', ..., 'n']
        """
        msg = 'Plugin is not implementing required method get_kb_location.'
        raise NotImplementedError(msg)

    def exploit(self, vuln_to_exploit=None):
        """
        Exploits a vuln that was found and stored in the kb.

        :param vuln_to_exploit: The vulnerability id to exploit
        :return: A list of shells of proxies generated by the exploitation phase
        """
        if not self.can_exploit():
            fmt = 'No %s vulnerabilities have been found.'
            msg = fmt % ' or '.join(self.get_kb_location())
            raise NoVulnerabilityFoundException(msg)

        om.out.information(self.get_name() + ' exploit plugin is starting.')
        generated_shells = []

        for vuln in self.get_exploitable_vulns():

            if vuln_to_exploit is not None:
                if vuln_to_exploit != vuln.get_id():
                    continue

            #
            #   A couple of minor verifications before continuing to exploit a
            #   vulnerability
            #
            if not isinstance(vuln.get_url(), URL):
                msg = '%s plugin can NOT exploit vulnerability with id "%s" as'\
                      ' it doesn\'t have an URL.'
                om.out.debug(msg % (self.get_name(), vuln.get_id()))
                continue

            if not isinstance(vuln.get_method(), basestring):
                msg = '%s plugin can NOT exploit vulnerability with id "%s" as'\
                      ' it doesn\'t have an HTTP method.'
                om.out.debug(msg % (self.get_name(), vuln.get_id()))
                continue

            # Try to get a shell using a vuln
            try:
                s = self._generate_shell(vuln)
            except (HTTPRequestException, ScanMustStopException,
                    ScanMustStopByUnknownReasonExc,
                    ScanMustStopByUserRequest) as e:
                # We get here when there were errors in the exploitation process
                # and we raise this custom exception to let the user know that
                # something went wrong.
                msg = 'The exploitation failed due to HTTP exception: "%s".'
                raise ExploitFailedException(msg % e)

            if s is not None:
                kb.kb.append(self.get_name(), 'shell', s)
                generated_shells.append(s)
                om.out.console('Vulnerability successfully exploited.'
                               ' Generated shell object %s' % s)
                if self._generate_only_one:
                    # A shell was generated, I only need one point of exec.
                    return [s, ]
                else:
                    # Keep adding all shells to the kb
                    # this is done 5 lines before this comment
                    pass

        return generated_shells

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one. For attack plugins this doesn't make much
                 sense since we're not doing anything with the output from this
                 method.
        """
        return []
