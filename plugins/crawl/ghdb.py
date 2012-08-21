'''
ghdb.py

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
import os.path
import xml.dom.minidom

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.misc.decorators import runonce
from core.controllers.misc.is_private_site import is_private_site
from core.controllers.w3afException import w3afException, w3afRunOnce
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.search_engines.google import \
    google as google
import core.controllers.outputManager as om
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln


class ghdb(CrawlPlugin):
    '''
    Search Google for vulnerabilities in the target site.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # Internal variables
        self._ghdb_file = os.path.join('plugins', 'crawl',
                                       'ghdb', 'GHDB.xml')
        
        # User configured variables
        self._result_limit = 300
    
    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request ):
        '''
        @param fuzzable_request: A fuzzable_request instance that contains
            (among other things) the URL to test.
        '''
        # Get the domain and set some parameters
        domain = fuzzable_request.getURL().getDomain()
        if is_private_site(domain):
            msg = 'There is no point in searching google for "site:'+ domain
            msg += '" . Google doesn\'t index private pages.'
            raise w3afException(msg)
        else:
            self._do_clasic_GHDB(domain)
        
    def _do_clasic_GHDB( self, domain ):
        '''
        In classic GHDB, i search google for every term in the ghdb.
        '''
        import random
        google_hack_list = self._read_ghdb() 
        # dont get discovered by google [at least try...]
        random.shuffle( google_hack_list )
        
        for gh in google_hack_list:
            try:
                self._classic_worker(gh, 'site:'+ domain + ' ' + gh.search)
            except w3afException, w3:
                # Google is saying: "no more automated tests".
                om.out.error('GHDB exception: "' + str(w3) + '".')
                break
        
        self._join()
    
    def _classic_worker(self, gh, search):
        
        # Init some variables
        google_se = google(self._uri_opener)
        
        google_list = google_se.getNResults( search, 9 )
        
        for result in google_list:
            # I found a vuln in the site!
            response = self._uri_opener.GET(result.URL, cache=True )
            if not is_404( response ):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURL( response.getURL() )
                v.setMethod( 'GET' )
                v.setName( 'Google hack database vulnerability' )
                v.setSeverity(severity.MEDIUM)
                msg = 'ghdb plugin found a vulnerability at URL: "' + result.URL
                msg += '" . Vulnerability description: ' + gh.desc
                v.setDesc( msg  )
                v.setId( response.id )
                kb.kb.append( self, 'vuln', v )
                om.out.vulnerability( v.getDesc(), severity=severity.MEDIUM )
                        
                # Create the fuzzable requests
                for fr in self._create_fuzzable_requests( response ):
                    self.output_queue.put(fr)
    
    def _read_ghdb( self ):
        '''
        Reads the ghdb.xml file and returns a list of google_hack objects.
        
        '''
        class google_hack:
            def __init__( self, search, desc ):
                self.search = search
                self.desc = desc
        
        fd = None
        try:
            fd = file( self._ghdb_file )
        except:
            raise w3afException('Failed to open ghdb file: ' + self._ghdb_file )
        
        dom = None
        try:
            dom = xml.dom.minidom.parseString( fd.read() )
        except:
            raise w3afException('ghdb file is not a valid XML file.' )
            
        signatures = dom.getElementsByTagName("signature")
        res = []
        
        
        for signature in signatures:
            if len(signature.childNodes) != 6:
                msg = 'GHDB is corrupt. The corrupt signature is: ' + signature.toxml()
                raise w3afException( msg )
            else:
                try:
                    query_string = signature.childNodes[4].childNodes[0].data
                    
                except Exception, e:
                    msg = 'GHDB has a corrupt signature, ( it doesn\'t have a query string ).'
                    msg += ' Error while parsing: "' + signature.toxml() + '". Exception: "'
                    msg += str(e) + '".'
                    om.out.debug( msg )
                else:
                    try:
                        desc = signature.childNodes[5].childNodes[0].data
                    except:
                        desc = 'Blank description.'
                    else:
                        gh = google_hack( query_string, desc )
                        res.append( gh )
          
        return res
        
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''        
        d2 = 'Fetch the first "resultLimit" results from the Google search'
        o2 = option('resultLimit', self._result_limit, d2, 'integer')

        ol = optionList()
        ol.add(o2)
        return ol

    def set_options( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._result_limit = optionsMap['resultLimit'].getValue()
            
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds possible vulnerabilities using google.
        
        One configurable parameter exist:
            - resultLimit
        
        Using the google hack database released by Offensive Security, this 
	plugin searches google for possible vulnerabilities in the domain
	being tested.
        '''
