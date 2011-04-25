'''
findvhost.py

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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.dpCache as dpCache
from core.controllers.misc.levenshtein import relative_distance_lt
from core.data.fuzzer.fuzzer import createRandAlNum
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.data.bloomfilter.pybloom import ScalableBloomFilter

import socket


class findvhost(baseDiscoveryPlugin):
    '''
    Modify the HTTP Host header and try to find virtual hosts.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._first_exec = True
        self._already_queried = ScalableBloomFilter()
        self._can_resolve_domain_names = False
        self._non_existant_response = None
        
    def discover(self, fuzzableRequest ):
        '''
        Find virtual hosts.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                    (among other things) the URL to test.
        '''
        vhost_list = []
        if self._first_exec:
            # Only run once
            self._first_exec = False
            vhost_list = self._generic_vhosts( fuzzableRequest )
            
            # Set this for later
            self._can_resolve_domain_names = self._can_resolve_domains()
            
        
        # I also test for ""dead links"" that the web programmer left in the page
        # For example, If w3af finds a link to "http://corporative.intranet.corp/" it will try to
        # resolve the dns name, if it fails, it will try to request that page from the server
        vhost_list.extend( self._get_dead_links( fuzzableRequest ) )
        
        # Report our findings
        for vhost, request_id in vhost_list:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( fuzzableRequest.getURL() )
            v.setMethod( 'GET' )
            v.setName( 'Shared hosting' )
            v.setSeverity(severity.LOW)
            
            domain = fuzzableRequest.getURL().getDomain()
            
            msg = 'Found a new virtual host at the target web server, the virtual host name is: "'
            msg += vhost + '". To access this site you might need to change your DNS resolution'
            msg += ' settings in order to point "' + vhost + '" to the IP address of "'
            msg += domain + '".'
            v.setDesc( msg )
            v.setId( request_id )
            kb.kb.append( self, 'findvhost', v )
            om.out.information( v.getDesc() )       
        
        return []
        
    def _get_dead_links(self, fuzzableRequest):
        '''
        Find every link on a HTML document verify if the domain is reachable or not; after that,
        verify if the web found a different name for the target site or if we found a new site that
        is linked. If the link points to a dead site then report it (it could be pointing to some 
        private address or something...)
        '''
        res = []
        
        # Get some responses to compare later
        base_url = fuzzableRequest.getURL().baseUrl()
        original_response = self._urlOpener.GET(fuzzableRequest.getURI(), useCache=True)
        base_response = self._urlOpener.GET(base_url, useCache=True)
        base_resp_body = base_response.getBody()
        
        try:
            dp = dpCache.dpc.getDocumentParserFor(original_response)
        except w3afException:
            # Failed to find a suitable parser for the document
            return []
        
        # Set the non existant response
        non_existant = 'iDoNotExistPleaseGoAwayNowOrDie' + createRandAlNum(4) 
        self._non_existant_response = self._urlOpener.GET(base_url, 
                                                useCache=False, headers={'Host': non_existant})
        nonexist_resp_body = self._non_existant_response.getBody()
        
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
        
        for link in parsed_references:
            domain = link.getDomain()
            
            #
            # First section, find internal hosts using the HTTP Host header:
            #
            if domain not in self._already_queried:
                # If the parsed page has an external link to www.google.com
                # then I'll send a request to the target site, with Host: www.google.com
                # This sucks, but it's cool if the document has a link to 
                # http://some.internal.site.target.com/
                try:
                    vhost_response = self._urlOpener.GET(base_url, useCache=False,
                                                         headers={'Host': domain })
                except w3afException:
                    pass
                else:
                    self._already_queried.add(domain)
                    vhost_resp_body = vhost_response.getBody()
                    
                    # If they are *really* different (not just different by some chars)
                    if relative_distance_lt(vhost_resp_body, base_resp_body, 0.35) and \
                        relative_distance_lt(vhost_resp_body, nonexist_resp_body, 0.35):
                        # and the domain can't just be resolved using a DNS query to
                        # our regular DNS server
                        report = True
                        if self._can_resolve_domain_names:
                            try:
                                socket.gethostbyname(domain)
                            except:
                                # aha! The HTML is linking to a domain that's
                                # hosted in the same server, and the domain name
                                # can NOT be resolved!
                                report = True
                            else:
                                report = False

                        # have found something interesting!
                        if report:
                            res.append( (domain, vhost_response.id) )

            #
            # Second section, find hosts using failed DNS resolutions
            #
            if self._can_resolve_domain_names:
                try:
                    # raises exception when it's not found
                    # socket.gaierror: (-5, 'No address associated with hostname')
                    socket.gethostbyname( domain )
                except:
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Internal hostname in HTML link')
                    i.setURL( fuzzableRequest.getURL() )
                    i.setMethod( 'GET' )
                    i.setId( original_response.id )
                    msg = 'The content of "'+ fuzzableRequest.getURL() +'" references a non '
                    msg += 'existant domain: "' + link + '". This may be a broken link, or an'
                    msg += ' internal domain name.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'findvhost', i )
                    om.out.information( i.getDesc() )
        
        res = [ r for r in res if r != '']
        
        return res 
    
    def _can_resolve_domains(self):
        '''
        This method was added to verify if w3af can resolve domain names
        using the OS configuration (/etc/resolv.conf in linux) or if we are in some
        strange LAN where we can't.
        
        @return: True if we can resolve domain names.
        '''
        try:
            socket.gethostbyname( 'www.w3.org' )
        except:
            return False
        else:
            return True
    
    def _generic_vhosts( self, fuzzableRequest ):
        '''
        Test some generic virtual hosts, only do this once.
        '''
        res = []
        base_url = fuzzableRequest.getURL().baseUrl()
        
        common_vhost_list = self._get_common_virtualhosts(base_url)
        
        # Get some responses to compare later
        original_response = self._urlOpener.GET(base_url, useCache=True)
        orig_resp_body = original_response.getBody()
        non_existant = 'iDoNotExistPleaseGoAwayNowOrDie' + createRandAlNum(4)
        self._non_existant_response = self._urlOpener.GET(base_url, useCache=False, \
                                                        headers={'Host': non_existant })
        nonexist_resp_body = self._non_existant_response.getBody()
        
        for common_vhost in common_vhost_list:
            try:
                vhost_response = self._urlOpener.GET( base_url, useCache=False, \
                                                headers={'Host': common_vhost } )
            except w3afException:
                pass
            else:
                vhost_resp_body = vhost_response.getBody()

                # If they are *really* different (not just different by some chars)
                if relative_distance_lt(vhost_resp_body, orig_resp_body, 0.35) and \
                    relative_distance_lt(vhost_resp_body, nonexist_resp_body, 0.35):
                    res.append((common_vhost, vhost_response.id))
        
        return res
    
    def _get_common_virtualhosts( self, base_url ):
        '''
        
        @parameter base_url: The target URL object. 
        
        @return: A list of possible domain names that could be hosted in the same web
        server that "domain".
                
        '''
        res = []
        domain = base_url.getDomain()
        root_domain = base_url.getRootDomain()
        
        common_virtual_hosts = ['intranet', 'intra', 'extranet', 'extra' , 'test' , 'test1'
        'old' , 'new' , 'admin', 'adm', 'webmail', 'services', 'console', 'apps', 'mail', 
        'corporate', 'ws', 'webservice', 'private', 'secure', 'safe', 'hidden', 'public' ]
        
        for subdomain in common_virtual_hosts:
            # intranet
            res.append( subdomain )
            # intranet.www.targetsite.com
            res.append( subdomain + '.' + domain )
            # intranet.targetsite.com
            res.append( subdomain + '.' + root_domain )
            # This is for:
            # intranet.targetsite
            res.append( subdomain + '.' + root_domain.split('.')[0] )
        
        return res

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin uses the HTTP Host header to find new virtual hosts. For example, if the
        intranet page is hosted in the same server that the public page, and the web server
        is misconfigured, this plugin will discover that virtual host.
        
        Please note that this plugin doesn't use any DNS technique to find this virtual hosts.
        '''
