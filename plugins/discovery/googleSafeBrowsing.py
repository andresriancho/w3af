'''
googleSafeBrowsing.py

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
from core.controllers.w3afException import w3afRunOnce
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.parsers.urlParser import *
import urllib
import socket

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

import os.path


class googleSafeBrowsing(baseDiscoveryPlugin):
    '''
    Search the Google Safe Browsing database to determine if your server is (or was) being used in phishing scams.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._run = True
        
        self._googleSafeBrowsingDB = 'http://sb.google.com/safebrowsing/update?version=goog-black-url:1:-1'
        
    def discover(self, fuzzableRequest ):
        self._fuzzableRequests = []
        
        if not self._run:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # Run one time
            self._run = False
            self._getDB()
            
            domain = getDomain( fuzzableRequest.getURL() )
            toCheckList = self._getToCheck( domain )
            
            googleSafeBrowsingMatches = self._isIngoogleSafeBrowsing( toCheckList )
            for url in googleSafeBrowsingMatches:
                response = self._urlOpener.GET( url )
                self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
                
                v = vuln.vuln()
                v.setURL( url )
                v.setId( response.id )
                v.setDesc( 'According to google safe browsing, the URL: ' + url + ' is involved in a phishing scam. ')
                om.out.vulnerability( v.getDesc() )
                
        return self._fuzzableRequests
        
    def _getToCheck( self, domain ):
        '''
        @return: From the domain, get a list of fqdn, rootDomain and IP address.
        '''
        res = []
        
        addrinfo = None
        try:
            addrinfo = socket.getaddrinfo( domain, 0)
        except:
            pass
        else:
            res.extend( [info[4][0] for info in addrinfo] )
        
        fqdn = ''
        try:
            fqdn = socket.getfqdn( domain )
        except:
            pass
        else:
            res.append( fqdn )
            
        rootDomain = ''
        try:
            rootDomain = getRootDomain( domain )
        except:
            om.out.debug( str(e) )
        else:
            res.append( rootDomain )
        
        res = list( set( res ) )
        return res
            
        
    def _isIngoogleSafeBrowsing( self, toCheckList ):
        '''
        Reads the googleSafeBrowsing db and tries to match the entries on that db with the toCheckList
        @return: A list with the sites to match against the googleSafeBrowsing db
        '''
        res = []
        for tc in toCheckList:
            for url in self._badURLList:
                if url.startswith('http://' + tc) or url.startswith('https://' + tc):
                    res.append( url )
        return res
        
    def setOptions( self, OptionsMap ):
        self._googleSafeBrowsingDB = OptionsMap['dbURL']
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'The URL to the google Safe Browsing database.'
        h1 = 'The default is ok in most cases.'
        o1 = option('dbURL', self._googleSafeBrowsingDB, d1, 'string', help=h1)
        
        ol = optionList()
        ol.add(o1)
        return ol

    def _getDB(self):
        '''
        This method is called to update the database.
        '''
        om.out.information('Trying to download the google safe browsing database, please wait...')
        response = self._urlOpener.GET( self._googleSafeBrowsingDB )
        om.out.information('Done downloading DB from google!')
        # Parsing list
        self._badURLList = re.findall( '\+(.*?)\t.*?\n', response.getBody() )
        
        
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
        This plugin searches the domain being tested in the google safe browsing database.
        If your site is in this database the chances are that you were hacked and your server is now being
        used in phishing attacks.
        '''
