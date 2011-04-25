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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln

from core.data.searchEngines.googleSearchEngine import googleSearchEngine as google
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.misc.is_private_site import is_private_site

from core.controllers.coreHelpers.fingerprint_404 import is_404
import core.data.constants.severity as severity

import os.path
import xml.dom.minidom


class ghdb(baseDiscoveryPlugin):
    '''
    Search Google for vulnerabilities in the target site.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._run = True
        self._ghdb_file = 'plugins' + os.path.sep + 'discovery' + os.path.sep
        self._ghdb_file += 'ghdb' + os.path.sep + 'GHDB.xml'
        self._update_URL = 'http://johnny.ihackstuff.com/xml/schema.xml'
        self._fuzzableRequests = []
        
        # User configured variables
        self._result_limit = 300
        self._update_ghdb = False
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
        if not self._run:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            
            # update !
            if self._update_ghdb:
                self._update_db()
                
            # I will only run this one time. All calls to ghdb return the same url's
            self._run = False
            
            # Get the domain and set some parameters
            domain = fuzzableRequest.getURL().getDomain()
            if is_private_site( domain ):
                msg = 'There is no point in searching google for "site:'+ domain
                msg += '" . Google doesnt index private pages.'
                raise w3afException( msg )
            
            return self._do_clasic_GHDB( domain )
        
        return []
    
    def _update_db( self ):
        '''
        New versions of the ghdb can be downloaded from: 
            - http://johnny.ihackstuff.com/xml/schema.xml
        '''
        # Only update once
        self._update_ghdb = False
        msg = 'Downloading the new google hack database from '+ self._update_URL
        msg += ' . This may take a while...'
        om.out.information( msg )
        res = self._urlOpener.GET( self._update_URL )
        try:
            # Write new ghdb
            fd_new_db = file( self._ghdb_file , 'w')
            fd_new_db.write( res.getBody() )
            fd_new_db.close()
        except:
            raise w3afException('There was an error while writing the new GHDB file to disk.')
        else:
            om.out.information('Successfully updated GHDB.xml.' )
            
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
        
        self._tm.join( self )
        
        return self._fuzzableRequests
    
    def _classic_worker(self, gh, search):
        
        # Init some variables
        google_se = google(self._urlOpener)
        
        google_list = google_se.getNResults( search, 9 )
        
        for result in google_list:
            # I found a vuln in the site!
            response = self._urlOpener.GET(result.URL, useCache=True )
            if not is_404( response ):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURL( response.getURL() )
                v.setMethod( 'GET' )
                v.setName( 'Google hack database vulnerability' )
                v.setSeverity(severity.MEDIUM)
                msg = 'ghdb plugin found a vulnerability at URL: ' + result.URL
                msg += ' . Vulnerability description: ' + gh.desc
                v.setDesc( msg  )
                v.setId( response.id )
                kb.kb.append( self, 'vuln', v )
                om.out.vulnerability( v.getDesc(), severity=severity.MEDIUM )
                        
                # Create the fuzzable requests
                self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
    
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
            if len(signature.childNodes) != 19:
                msg = 'GHDB is corrupt. The corrupt signature is: ' + signature.toxml()
                raise w3afException( msg )
            else:
                try:
                    query_string = signature.childNodes[9].childNodes[0].data
                except Exception, e:
                    msg = 'GHDB has a corrupt signature, ( it doesn\'t have a query string ).'
                    msg += ' Error while parsing: "' + signature.toxml() + '". Exception: "'
                    msg += str(e) + '".'
                    om.out.debug( msg )
                else:
                    try:
                        desc = signature.childNodes[13].childNodes[0].data
                    except:
                        desc = 'Blank description.'
                    else:
                        gh = google_hack( query_string, desc )
                        res.append( gh )
            
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''        
        d2 = 'Fetch the first "resultLimit" results from the Google search'
        o2 = option('resultLimit', self._result_limit, d2, 'integer')
        
        # The ghdb is not online anymore, updating may brake this plugin.
        # http://johnny.ihackstuff.com/HFC/Home.html
        #
        #d3 = 'Update the google hack database.'
        #o3 = option('updateGHDB', self._update_ghdb, d3, 'boolean')
        
        ol = optionList()
        ol.add(o2)
        #ol.add(o3)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        # The ghdb is not online anymore, updating may brake this plugin.
        # http://johnny.ihackstuff.com/HFC/Home.html
        #
        #self._update_ghdb = optionsMap['updateGHDB'].getValue()
        self._result_limit = optionsMap['resultLimit'].getValue()
            
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
        This plugin finds possible vulnerabilities using google.
        
        Three configurable parameters exist:
            - resultLimit
            - updateGHDB
        
        Using the google hack database released by jhonny, this plugin searches google for possible
        vulnerabilities in the domain being tested.
        '''
