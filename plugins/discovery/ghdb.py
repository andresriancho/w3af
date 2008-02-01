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
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.searchEngines.google import google as google
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.urlParser as urlParser
import core.data.constants.severity as severity

import os.path
import re
import xml.dom.minidom

class ghdb(baseDiscoveryPlugin):
    '''
    Search Google for vulnerabilities in the target site.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._run = True
        self._ghdbFile = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'ghdb' + os.path.sep + 'GHDB.xml'
        self._updateURL = 'http://johnny.ihackstuff.com/xml/schema.xml'
        
        # User configured variables
        self._key = ''
        self._resultLimit = 300
        self._updateGHDB = False
        
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
            if self._updateGHDB:
                self._updateDb()
                
            # I will only run this one time. All calls to ghdb return the same url's
            self._run = False
            
            # Init some internal variables
            self.is404 = kb.kb.getData( 'error404page', '404' )
            self._google = google( self._urlOpener, self._key )
            
            # Get the domain and set some parameters
            domain = urlParser.getDomain( fuzzableRequest.getURL() )
            if self._google.isPrivate( domain ):
                raise w3afException('There is no point in searching google for "site:'+ domain + '" . Google doesnt index private pages.')
            
            return self._doClasicGHDB( domain )
        
        return []
    
    def _updateDb( self ):
        '''
        New versions of the ghdb can be downloaded from: 
            - http://johnny.ihackstuff.com/xml/schema.xml
        '''
        # Only update once
        self._updateGHDB = False
        om.out.information('Downloading the new google hack database from '+ self._updateURL+' . This may take a while...')
        res = self._urlOpener.GET( self._updateURL )
        try:
            # Write new ghdb
            fdNewDb = file( self._ghdbFile , 'w')
            fdNewDb.write( res.getBody() )
            fdNewDb.close()
        except:
            raise w3afException('There was an error while writing the new GHDB file to disk.')
        else:
            om.out.information('Successfully updated GHDB.xml.' )
            
    def _doReverseGHDB( self, domain ):
        '''
        In reverse ghdb, i search for site:domain , fetch every page one by one
        and try MYSELF to match the query thats on the ghdb with the result.
        '''
        googleList = self._google.getNResults('site:'+ domain, self._resultLimit )
        for url in googleList:
            response = self._urlOpener.GET(result.URL, useCache=True )
            if not self.is404( response ):
                for gh in self._readGhdb():
                    if self._reverseMatch( gh, response ):
                        v = vuln.vuln()
                        v.setURL( response.getURL() )
                        v.setMethod( 'GET' )
                        v.setName( 'Google hack database vulnerability' )
                        v.setSeverity(severity.MEDIUM)                        
                        v.setDesc( 'ghdb plugin found a vulnerability at URL: ' + v.getURL() + ' . Vulnerability description: ' + gh.desc )
                        v.setId( response.id )
                        kb.kb.append( self, 'vuln', v )
                        om.out.vulnerability( v.getDesc() )
                        
                        # Create the fuzzable requests
                        self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
        
        return self._fuzzableRequests
        
    def _reverseMatch( self, gh, response ):
        '''
        Do a reverse search !
        '''
        urlRegex, bodyRegex = self._createRegexs( gh )
        if urlRegex.match( response.getURI() ) and bodyRegex.match( response.getBody ):
            return True
        else:
            return False
            
    def _createRegexs( gh ):
        '''
        Create a regular expression based on a google search
        @return: A tuple with ( urlRegex, bodyRegex )
        '''
        reservedWords = ['allintitle','allinurl','ext','filetype','intext','intitle','inurl']
        searchMap = {}
        for rword in reservedWords:
            res = re.findall( rword + ':(".*"|[^ ]+)', gh)
            '''
            >>> re.findall( 'inurl:(".*"|[^ ]+)', 'inurl:pepe inurl:"add me"')
            ['pepe', '"add me"']
            '''
            # Now i'll kill the double quotes
            tmp = []
            for i in res:
                if i[0] == '"':
                    i = i[1:]
                if i[-1:] == '"':
                    i = i[:-1]
                tmp.append( i )
            res = tmp
            searchMap[ rword ] = tmp
            
        # Done, all restricted words and their values have been added to the list
        # Now, based on the map, I'll create the regexes !
        urlSearches = ['allinurl','ext','filetype','inurl']
        if len( set( searchMap.keys() ).intersection( set(urlSearches) ) ) == 0:
            urlRegex = '.*'
        else:
            # Damn i have to work :(
            pass
        
        bodyRegex = '.*'
            
    def _doClasicGHDB( self, domain ):
        '''
        In classic GHDB, i search google for every term in the ghdb.
        '''
        import random
        googleHackList = self._readGhdb() 
        # dont get discovered by google [at least try...]
        random.shuffle( googleHackList )
        
        for gh in googleHackList:
            targs = ( gh, 'site:'+ domain + ' ' + gh.search )
            self._tm.startFunction( target=self._classicWorker, args=targs, ownerObj=self )
        
        self._tm.join( self )
        
        return self._fuzzableRequests
    
    def _classicWorker( self, gh, search ):
            googleList = self._google.getNResults( search, 9 )
            
            for result in googleList:
                # I found a vuln in the site!
                response = self._urlOpener.GET(result.URL, useCache=True )
                if not self.is404( response ):
                    v = vuln.vuln()
                    v.setURL( response.getURL() )
                    v.setMethod( 'GET' )
                    v.setName( 'Google hack database vulnerability' )
                    v.setSeverity(severity.MEDIUM)
                    v.setDesc( 'ghdb plugin found a vulnerability at URL: ' + result.URL + ' . Vulnerability description: ' + gh.desc )
                    v.setId( response.id )
                    kb.kb.append( self, 'vuln', v )
                    om.out.vulnerability( v.getDesc() )
                            
                    # Create the fuzzable requests
                    self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
    
    def _readGhdb( self ):
        '''
        Reads the ghdb.xml file and returns a list of googleHack objects.
        
        '''
        class googleHack:
            def __init__( self, search, desc ):
                self.search = search
                self.desc = desc
        
        fd = None
        try:
            fd = file( self._ghdbFile )
        except:
            raise w3afException('Failed to open ghdb file: ' + self._ghdbFile )
        
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
                    queryString = signature.childNodes[9].childNodes[0].data
                except Exception, e:
                    msg = 'GHDB has a corrupt signature, ( it doesn\'t have a queryString ). Error while parsing: ' + signature.toxml()
                    om.out.debug( msg )
                else:
                    try:
                        desc = signature.childNodes[13].childNodes[0].data
                    except:
                        desc = 'Blank description.'
                    else:
                        gh = googleHack( queryString, desc )
                        res.append( gh )
            
        return res
            
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="key">\
                <default>'+str(self._key)+'</default>\
                <desc>Google API License key</desc>\
                <type>string</type>\
                <help>To use this plugin you have to own your own google API license key OR you can directly use the search engine using clasic HTTP. If this parameter is left blank, the search engine will be used, otherwise the google webservice will be used.Go to http://www.google.com/apis/ to get more information.</help>\
            </Option>\
            <Option name="resultLimit">\
                <default>'+str(self._resultLimit)+'</default>\
                <desc>Fetch the first "resultLimit" results from the Google search</desc>\
                <type>integer</type>\
                <help></help>\
            </Option>\
            <Option name="updateGHDB">\
                <default>'+str(self._updateGHDB)+'</default>\
                <desc>Update the google hack database.</desc>\
                <type>boolean</type>\
                <help></help>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._key = optionsMap['key']           
        self._updateGHDB = optionsMap['updateGHDB']
        self._resultLimit = optionsMap['resultLimit']
            
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
            - key
        
        Using the google hack database released by jhonny, this plugin searches google for possible
        vulnerabilities in the domain being tested.
        '''
