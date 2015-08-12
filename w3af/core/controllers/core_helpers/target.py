"""
target.py

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
import urllib2

import w3af.core.data.kb.config as cf
from w3af.core.controllers.configurable import Configurable
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList

cf.cf.save('targets', [])
cf.cf.save('target_domains', set())
cf.cf.save('baseURLs', [])


class CoreTarget(Configurable):
    """
    A class that acts as an interface for the user interfaces, so they can
    configure the target settings using get_options and SetOptions.
    """

    def __init__(self):
        # Set defaults for user configured variables
        self.clear()

        # Some internal variables
        self._operating_systems = ['unknown', 'unix', 'windows']
        self._programming_frameworks = ['unknown', 'php', 'asp', 'asp.net',
                                        'java', 'jsp', 'cfm', 'ruby', 'perl']

    def clear(self):
        cf.cf.save('targets', [])
        cf.cf.save('target_os', 'unknown')
        cf.cf.save('target_framework', 'unknown')
        cf.cf.save('target_domains', set())
        cf.cf.save('baseURLs', [])

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        targets = ','.join(str(tar) for tar in cf.cf.get('targets'))
        d = 'A comma separated list of URLs'
        o = opt_factory('target', targets, d, 'url_list')
        ol.add(o)

        d = 'Target operating system (%s)' % '/'.join(self._operating_systems)
        h = 'This setting is here to enhance w3af performance.'

        # This list "hack" has to be done because the default value is the one
        # in the first position on the list
        tmp_list = self._operating_systems[:]
        tmp_list.remove(cf.cf.get('target_os'))
        tmp_list.insert(0, cf.cf.get('target_os'))
        o = opt_factory('target_os', tmp_list, d, 'combo', help=h)
        ol.add(o)

        frameworks = '/'.join(self._programming_frameworks)
        d = 'Target programming framework (%s)' % frameworks
        h = 'This setting is here to enhance w3af performance.'
        # This list "hack" has to be done because the default value is the one
        # in the first position on the list
        tmp_list = self._programming_frameworks[:]
        tmp_list.remove(cf.cf.get('target_framework'))
        tmp_list.insert(0, cf.cf.get('target_framework'))
        o = opt_factory('target_framework', tmp_list, d, 'combo', help=h)
        ol.add(o)

        return ol

    def _verify_url(self, target_url, file_target=True):
        """
        Verify if the URL is valid and raise an exception if w3af doesn't
        support it.

        :param target_url: The target URL object to check if its valid or not.
        :return: None. A BaseFrameworkException is raised on error.
        """
        protocol = target_url.get_protocol()
        is_file = file_target and protocol == 'file'
        is_http = protocol in ('http', 'https') and target_url.is_valid_domain()
                
        if not is_file and not is_http:
            msg = ('Invalid format for target URL "%s", you have to specify '
                   'the protocol (http/https/file) and a domain or IP address.'
                   ' Examples: http://host.tld/ ; https://127.0.0.1/ .')
            raise BaseFrameworkException(msg % target_url)
        
        return True

    def get_urls_from_target(self, options_list):
        """
        Parse the user's input to extract the URLs

        :param options_list: The user configuration
        :return: A list with target URLs
        """
        configured_target_urls = options_list['target'].get_value()
        target_urls = []
        
        for target_url in configured_target_urls:

            self._verify_url(target_url)

            if not target_url.url_string.startswith('file:///'):
                # It's a common URL just like http://w3af.com/
                target_urls.append(target_url)
                
            else:
                try:
                    f = urllib2.urlopen(target_url.url_string)
                except:
                    msg = 'Cannot open target file: "%s"'
                    raise BaseFrameworkException(msg % target_url)
                else:
                    for line in f:
                        target_in_file = line.strip()

                        # Empty lines are allowed
                        if not target_in_file:
                            continue

                        # Comments starting with # are allowed too
                        if target_in_file.startswith('#'):
                            continue

                        try:
                            target_in_file_inst = URL(target_in_file)
                        except ValueError as ve:
                            # The URLs specified inside the file might be
                            # invalid, and the pieces of code which consume
                            # this method only handle BaseFrameworkException
                            #
                            # https://github.com/andresriancho/w3af/issues/12006
                            #
                            msg = ('The target URL "%s" specified inside the'
                                   ' target file "%s" is invalid: "%s"')
                            args = (target_in_file, target_url, ve)
                            raise BaseFrameworkException(msg % args)

                        # Some more validation before we're done...
                        self._verify_url(target_in_file_inst, file_target=False)
                        target_urls.append(target_in_file_inst)

                    f.close()

        return target_urls

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        target_urls = self.get_urls_from_target(options_list)

        # Now we perform a check to see if the user has specified more than
        # one target domain, for example: "http://google.com, http://yahoo.com".
        domain_list = [target_url.get_net_location() for target_url in
                       target_urls]
        domain_list = list(set(domain_list))
        
        if len(domain_list) > 1:
            msg = ('You specified more than one target domain: %s.'
                   ' And w3af can only scan one target domain at a time.')
            raise BaseFrameworkException(msg % ', '.join(domain_list))

        # This doesn't seem to be possible with the current framework design,
        # since we need "empty" targets to be an option for profiles
        #
        #if len(domain_list) == 0:
        #    msg = ('There is something wrong with the configured target URLs,'
        #           ' w3af was unable to extract at least one domain name from'
        #           ' the user configured setting: "%s"')
        #    configured_target_urls = options_list['target'].get_value()
        #    raise BaseFrameworkException(msg % configured_target_urls)

        # Save in the config, the target URLs, this may be useful for some
        # plugins
        cf.cf.save('targets', target_urls)
        cf.cf.save('target_domains', list(set([u.get_domain() for u in target_urls])))
        cf.cf.save('baseURLs', [i.base_url() for i in target_urls])

        # Advanced target selection
        os = options_list['target_os'].get_value_str()
        if os.lower() in self._operating_systems:
            cf.cf.save('target_os', os.lower())
        else:
            msg = u'Unknown target operating system: "%s"'
            raise BaseFrameworkException(msg % os)

        pf = options_list['target_framework'].get_value_str()
        if pf.lower() in self._programming_frameworks:
            cf.cf.save('target_framework', pf.lower())
        else:
            msg = u'Unknown target programming framework: "%s"'
            raise BaseFrameworkException(msg % pf)

    def get_name(self):
        return 'target_settings'

    def get_desc(self):
        return 'Configure target URLs'

    def has_valid_configuration(self):
        return cf.cf.get('targets') and cf.cf.get('target_domains')
