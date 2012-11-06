'''
find_vhosts.py

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
import socket

from itertools import izip, repeat

import core.controllers.outputManager as om
import core.data.parsers.dpCache as dpCache
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.controllers.misc.levenshtein import relative_distance_lt
from core.controllers.w3afException import w3afException
from core.controllers.threads.threadpool import return_args, one_to_many

from core.data.fuzzer.fuzzer import rand_alnum
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.dc.headers import Headers


class find_vhosts(InfrastructurePlugin):
    '''
    Modify the HTTP Host header and try to find virtual hosts.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        InfrastructurePlugin.__init__(self)
        
        # Internal variables
        self._first_exec = True
        self._already_queried = scalable_bloomfilter()
        self._can_resolve_domain_names = False
        
    def discover(self, fuzzable_request ):
        '''
        Find virtual hosts.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        analysis_result = self._analyze(fuzzable_request)
        self._report_results( fuzzable_request, analysis_result )
    
    def _analyze(self, fuzzable_request):
        vhost_list = []
        if self._first_exec:
            self._first_exec = False
            vhost_list.extend( self._generic_vhosts( fuzzable_request ) )
        
        # I also test for ""dead links"" that the web programmer left in the page
        # For example, If w3af finds a link to "http://corporative.intranet.corp/"
        # it will try to resolve the dns name, if it fails, it will try to request
        # that page from the server
        vhost_list.extend( self._get_dead_links( fuzzable_request ) )
        return vhost_list

    def _report_results(self, fuzzable_request, analysis_result):
        '''
        Report our findings
        '''
        reported = set()
        for vhost, request_id in analysis_result:
            if vhost not in reported:
                reported.add(vhost)
                v = vuln.vuln()
                v.setPluginName(self.get_name())
                v.setURL( fuzzable_request.getURL() )
                v.setMethod( 'GET' )
                v.set_name( 'Shared hosting' )
                v.setSeverity(severity.LOW)
                
                domain = fuzzable_request.getURL().getDomain()
                
                msg = 'Found a new virtual host at the target web server, the ' \
                      'virtual host name is: "' + vhost + '". To access this site' \
                      ' you might need to change your DNS resolution settings in' \
                      ' order to point "' + vhost + '" to the IP address of "' \
                      + domain + '".'
                v.set_desc( msg )
                v.set_id( request_id )
                kb.kb.append( self, 'find_vhosts', v )
                om.out.information( v.get_desc() )       
        
    def _get_dead_links(self, fuzzable_request):
        '''
        Find every link on a HTML document verify if the domain is reachable or 
        not; after that, verify if the web found a different name for the target
        site or if we found a new site that is linked. If the link points to a
        dead site then report it (it could be pointing to some private address
        or something...)
        '''
        # Get some responses to compare later
        base_url = fuzzable_request.getURL().baseUrl()
        original_response = self._uri_opener.GET(fuzzable_request.getURI(), cache=True)
        base_response = self._uri_opener.GET(base_url, cache=True)
        base_resp_body = base_response.getBody()
        
        try:
            dp = dpCache.dpc.getDocumentParserFor(original_response)
        except w3afException:
            # Failed to find a suitable parser for the document
            return []
        
        # Set the non existant response
        non_existant_response = self._get_non_exist(fuzzable_request)
        nonexist_resp_body = non_existant_response.getBody()
        
        # Note:
        # - With parsed_references I'm 100% that it's really something in the HTML
        # that the developer intended to add.
        #
        # - The re_references are the result of regular expressions, which in some cases
        # are just false positives.
        #
        # In this case, and because I'm only going to use the domain name of the URL
        # I'm going to trust the re_references also.
        parsed_references, re_references = dp.getReferences()
        parsed_references.extend(re_references)
        
        res = []
        
        vhosts = self._verify_link_domain(parsed_references)

        for domain, vhost_response in self._send_in_threads(base_url, vhosts):
        
            vhost_resp_body = vhost_response.getBody()

            if relative_distance_lt(vhost_resp_body, base_resp_body, 0.35) and \
            relative_distance_lt(vhost_resp_body, nonexist_resp_body, 0.35):
                res.append( (domain, vhost_response.id) )
            else:
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('Internal hostname in HTML link')
                i.setURL( fuzzable_request.getURL() )
                i.setMethod( 'GET' )
                i.set_id( original_response.id )
                msg = 'The content of "'+ fuzzable_request.getURL() +'" references a non '
                msg += 'existant domain: "' + domain + '". This may be a broken link, or an'
                msg += ' internal domain name.'
                i.set_desc( msg )
                kb.kb.append( self, 'find_vhosts', i )
                om.out.information( i.get_desc() )
                
        
        return res

    def _verify_link_domain(self, parsed_references):
        '''
        Verify each link in parsed_references and yield the ones that can NOT
        be resolved using DNS.
        '''
        for link in parsed_references:
            domain = link.getDomain()
            
            if domain not in self._already_queried:
                self._already_queried.add(domain)
                
                try:
                    # raises exception when it's not found
                    # socket.gaierror: (-5, 'No address associated with hostname')
                    socket.gethostbyname( domain )
                except:
                    yield domain
    
    def _generic_vhosts( self, fuzzable_request ):
        '''
        Test some generic virtual hosts, only do this once.
        '''
        # Get some responses to compare later
        base_url = fuzzable_request.getURL().baseUrl()
        original_response = self._uri_opener.GET(base_url, cache=True)
        orig_resp_body = original_response.getBody()

        non_existant_response = self._get_non_exist( fuzzable_request )
        nonexist_resp_body = non_existant_response.getBody()
        
        res = []
        vhosts = self._get_common_virtualhosts(base_url)
        
        for vhost, vhost_response in self._send_in_threads(base_url, vhosts):
            vhost_resp_body = vhost_response.getBody()

            # If they are *really* different (not just different by some chars)
            if relative_distance_lt(vhost_resp_body, orig_resp_body, 0.35) and \
            relative_distance_lt(vhost_resp_body, nonexist_resp_body, 0.35):
                res.append((vhost, vhost_response.id))
        
        return res
    
    def _send_in_threads(self, base_url, vhosts):
        base_url_repeater = repeat(base_url)
        args_iterator = izip(base_url_repeater, vhosts)
        http_get = return_args(one_to_many(self._http_get_vhost))
        pool_results = self._tm.threadpool.imap_unordered(http_get,
                                                          args_iterator)
        
        for ((base_url, vhost),), vhost_response in pool_results:
            yield vhost, vhost_response
    
    def _http_get_vhost(self, base_url, vhost):
        '''
        Performs an HTTP GET to a URL using a specific vhost.
        @return: HTTPResponse object.
        '''
        headers = Headers([('Host', vhost)])
        return self._uri_opener.GET( base_url, cache=False, \
                                     headers=headers )
    
    def _get_non_exist(self, fuzzable_request):
        base_url = fuzzable_request.getURL().baseUrl()
        non_existant_domain = 'iDoNotExistPleaseGoAwayNowOrDie' + rand_alnum(4) 
        return self._http_get_vhost(base_url, non_existant_domain)
    
    def _get_common_virtualhosts( self, base_url ):
        '''
        
        @parameter base_url: The target URL object. 
        
        @return: A list of possible domain names that could be hosted in the same web
        server that "domain".
                
        '''
        domain = base_url.getDomain()
        root_domain = base_url.getRootDomain()
        
        common_virtual_hosts = ['intranet', 'intra', 'extranet', 'extra' ,
                                'test' , 'test1', 'old' , 'new' , 'admin',
                                'adm', 'webmail', 'services', 'console',
                                'apps', 'mail', 'corporate', 'ws', 'webservice',
                                'private', 'secure', 'safe', 'hidden', 'public' ]
        
        for subdomain in common_virtual_hosts:
            # intranet
            yield subdomain
            # intranet.www.targetsite.com
            yield subdomain + '.' + domain
            # intranet.targetsite.com
            yield subdomain + '.' + root_domain
            # intranet.targetsite
            yield subdomain + '.' + root_domain.split('.')[0]
        
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin uses the HTTP Host header to find new virtual hosts. For
        example, if the intranet page is hosted in the same server that the 
        public page, and the web server is misconfigured, this plugin will
        discover that virtual host.
        
        Please note that this plugin doesn't use any DNS technique to find 
        these virtual hosts.
        '''
