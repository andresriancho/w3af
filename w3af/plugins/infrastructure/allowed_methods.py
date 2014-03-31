"""
allowed_methods.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.response_codes as response_codes

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.group_by_min_key import group_by_min_key
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.info import Info


class allowed_methods(InfrastructurePlugin):
    """
    Enumerate the allowed methods of an URL.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    BAD_CODES = set(
        [response_codes.UNAUTHORIZED, response_codes.NOT_IMPLEMENTED,
         response_codes.METHOD_NOT_ALLOWED, response_codes.FORBIDDEN])

    DAV_METHODS = set(
        ['DELETE', 'PROPFIND', 'PROPPATCH', 'COPY', 'MOVE', 'LOCK',
         'UNLOCK', 'MKCOL'])
    COMMON_METHODS = set(['OPTIONS', 'GET', 'HEAD', 'POST', 'TRACE', 'PUT'])
    UNCOMMON_METHODS = set(['*', 'SUBSCRIPTIONS', 'NOTIFY', 'DEBUG', 'TRACK',
                            'POLL', 'PIN', 'INVOKE', 'SUBSCRIBE', 'UNSUBSCRIBE'])
    # Methods taken from http://www.w3.org/Protocols/HTTP/Methods.html
    PROPOSED_METHODS = set(
        ['CHECKOUT', 'SHOWMETHOD', 'LINK', 'UNLINK', 'CHECKIN',
         'TEXTSEARCH', 'SPACEJUMP', 'SEARCH', 'REPLY'])
    EXTRA_METHODS = set(
        ['CONNECT', 'RMDIR', 'MKDIR', 'REPORT', 'ACL', 'DELETE',
         'INDEX', 'LABEL', 'INVALID'])
    VERSION_CONTROL = set(['VERSION_CONTROL', 'CHECKIN', 'UNCHECKOUT', 'PATCH',
                           'MERGE', 'MKWORKSPACE', 'MKACTIVITY', 'BASELINE_CONTROL'])

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._exec = True
        self._already_tested = ScalableBloomFilter()

        # Methods
        self._supported_methods = self.DAV_METHODS | self.COMMON_METHODS | \
            self.UNCOMMON_METHODS | self.PROPOSED_METHODS | \
            self.EXTRA_METHODS | self.VERSION_CONTROL

        # User configured variables
        self._exec_one_time = True
        self._report_dav_only = True

    def discover(self, fuzzable_request):
        """
        Uses several techniques to try to find out what methods are allowed for
        an URL.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        if not self._exec:
            # This will remove the plugin from the infrastructure
            # plugins to be run.
            raise RunOnce()

        # Run the plugin.
        if self._exec_one_time:
            self._exec = False

        domain_path = fuzzable_request.get_url().get_domain_path()
        if domain_path not in self._already_tested:
            self._already_tested.add(domain_path)
            allowed_methods, id_list = self._identify_allowed_methods(domain_path)
            self._analyze_methods(domain_path, allowed_methods, id_list)

    def _identify_allowed_methods(self, url):
        # First, try to check available methods using OPTIONS,
        # if OPTIONS isn't enabled, do it manually
        allowed_options, id_options = self._identify_with_OPTIONS(url)
        allowed_bf, id_bf = self._identify_with_bruteforce(url)
        
        allowed_methods = allowed_options + allowed_bf
        id_list = id_options + id_bf
        
        # Added this to make the output a little bit more readable.
        allowed_methods.sort()
        
        return allowed_methods, id_list
        
        
    def _identify_with_OPTIONS(self, url):
        """
        Find out what methods are allowed using OPTIONS
        :param url: Where to check.
        """
        allowed_methods = []
        id_list = []

        try:
            res = self._uri_opener.OPTIONS(url)
        except:
            pass
        else:
            headers = res.get_lower_case_headers()
            id_list.append(res.id)
            
            for header_name in ['allow', 'public']:
                if header_name in headers:
                    allowed_methods.extend(headers[header_name].split(','))
                    allowed_methods = [x.strip() for x in allowed_methods]
                    allowed_methods = list(set(allowed_methods))
        
        return allowed_methods, id_list
            
    
    def _identify_with_bruteforce(self, url):
        id_list = []
        allowed_methods = []
        #
        #   Before doing anything else, I'll send a request with a
        #   non-existant method if that request succeds, then all will...
        #
        non_exist_response = self._uri_opener.ARGENTINA(url)
        get_response = self._uri_opener.GET(url)

        if non_exist_response.get_code() not in self.BAD_CODES\
        and get_response.get_body() == non_exist_response.get_body():

            desc = 'The remote Web server has a custom configuration, in'\
                  ' which any not implemented methods that are invoked are'\
                  ' defaulted to GET instead of returning a "Not Implemented"'\
                  ' response.'
            response_ids = [non_exist_response.get_id(), get_response.get_id()]
            i = Info('Non existent methods default to GET', desc, response_ids,
                     self.get_name())
            i.set_url(url)
            
            kb.kb.append(self, 'custom-configuration', i)
            #
            #   It makes no sense to continue working, all methods will
            #   appear as enabled because of this custom configuration.
            #
            return [], [non_exist_response.id, get_response.id]

        # 'DELETE' is not tested! I don't want to remove anything...
        # 'PUT' is not tested! I don't want to overwrite anything...
        methods_to_test = self._supported_methods.copy()

        # remove dangerous methods.
        methods_to_test.remove('DELETE')
        methods_to_test.remove('PUT')

        for method in methods_to_test:
            method_functor = getattr(self._uri_opener, method)
            try:
                response = apply(method_functor, (url,), {})
            except:
                pass
            else:
                code = response.get_code()                
                if code not in self.BAD_CODES:
                    allowed_methods.append(method)
                    id_list.append(response.id)
        
        return allowed_methods, id_list

    def _analyze_methods(self, url, allowed_methods, id_list):
        # Check for DAV
        if set(allowed_methods).intersection(self.DAV_METHODS):
            # dav is enabled!
            # Save the results in the KB so that other plugins can use this
            # information
            desc = 'The URL "%s" has the following allowed methods. These'\
                  ' include DAV methods and should be disabled: %s' 
            desc = desc % (url, ', '.join(allowed_methods))
            
            i = Info('DAV methods enabled', desc, id_list, self.get_name())
            i.set_url(url)
            i['methods'] = allowed_methods
            
            kb.kb.append(self, 'dav-methods', i)
        else:
            # Save the results in the KB so that other plugins can use this
            # information. Do not remove these information, other plugins
            # REALLY use it !
            desc = 'The URL "%s" has the following enabled HTTP methods: %s'
            desc = desc % (url, ', '.join(allowed_methods))
            
            i = Info('Allowed HTTP methods', desc, id_list, self.get_name())
            i.set_url(url)
            i['methods'] = allowed_methods
            
            kb.kb.append(self, 'methods', i)
            

    def end(self):
        """
        Print the results.
        """
        # First I get the data from the kb
        all_info_obj = kb.kb.get('allowed_methods', 'methods')
        dav_info_obj = kb.kb.get('allowed_methods', 'dav-methods')

        # Now I transform it to something I can use with group_by_min_key
        allMethods = []
        for i in all_info_obj:
            allMethods.append((i.get_url(), i['methods']))

        davMethods = []

        for i in dav_info_obj:
            davMethods.append((i.get_url(), i['methods']))

        # Now I work the data...
        to_show, method_type = davMethods, ' DAV'
        if not self._report_dav_only:
            to_show, method_type = allMethods, ''

        # Make it hashable
        tmp = []
        for url, methodList in to_show:
            tmp.append((url, ', '.join(methodList)))

        result_dict, itemIndex = group_by_min_key(tmp)

        for k in result_dict:
            if itemIndex == 0:
                # Grouped by URLs
                msg = 'The URL: "%s" has the following' + \
                    method_type + ' methods enabled:'
                om.out.information(msg % k)
            else:
                # Grouped by Methods
                msg = 'The methods: ' + k + \
                    ' are enabled on the following URLs:'
                om.out.information(msg)

            for i in result_dict[k]:
                om.out.information('- ' + i)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d1 = 'Execute plugin only one time'
        h1 = 'Generally the methods allowed for a URL are configured system'\
             ' wide, so executing this plugin only once is the faster choice.'\
             ' The most accurate choice is to run it against every URL.'
        o = opt_factory('execOneTime', self._exec_one_time, d1,
                        'boolean', help=h1)
        ol.add(o)

        d2 = 'Only report findings if uncommon methods are found'
        o = opt_factory('reportDavOnly', self._report_dav_only, d2, 'boolean')
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        :param OptionList: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._exec_one_time = options_list['execOneTime'].get_value()
        self._report_dav_only = options_list['reportDavOnly'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds which HTTP methods are enabled for a URI.

        Two configurable parameters exist:
            - execOneTime
            - reportDavOnly

        If "execOneTime" is set to True, then only the methods in the webroot are
        enumerated. If "reportDavOnly" is set to True, this plugin will only
        report the enabled method list if DAV methods have been found.

        The plugin will try to use the OPTIONS method to enumerate all available
        methods, if that fails, a manual enumeration is done.
        """
