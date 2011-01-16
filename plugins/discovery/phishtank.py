'''
phishtank.py

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
from core.controllers.w3afException import w3afRunOnce, w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
from core.data.parsers.urlParser import url_object

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os.path
import socket


class phishtank(baseDiscoveryPlugin):
    '''
    Search the phishtank.com database to determine if your server is (or was) being used in phishing scams.
    
    @author: Andres Riancho ( andres.riancho@gmail.com ) ; special thanks to http://www.phishtank.com/ !
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._run = True

        # Internal variables
        self._fuzzable_requests = []
        
        # User defines variable
        self._phishtank_DB = 'plugins' + os.path.sep + 'discovery'
        self._phishtank_DB += os.path.sep + 'phishtank' + os.path.sep + 'index.xml'
        self._update_DB = False
        
    def discover(self, fuzzableRequest ):
        '''
        Plugin entry point, perform all the work.
        '''
        
        if not self._run:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # Run one time
            self._run = False
            
            if self._update_DB:
                self._do_update()
            
            to_check_list = self._get_to_check( fuzzableRequest.getURL() )
            
            # I found some URLs, create fuzzable requests
            phishtank_matches = self._is_in_phishtank( to_check_list )
            for ptm in phishtank_matches:
                response = self._urlOpener.GET( ptm.url )
                self._fuzzable_requests.extend( self._createFuzzableRequests( response ) )
            
            # Only create the vuln object once
            if phishtank_matches:
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURL( ptm.url )
                v.setId( response.id )
                v.setName( 'Phishing scam' )
                v.setSeverity(severity.LOW)
                desc = 'The URL: "' + ptm.url + '" seems to be involved in a phishing scam. Please see "'
                desc += ptm.more_info_URL + '" for more info.'
                v.setDesc( desc )
                kb.kb.append( self, 'phishtank', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                
        return self._fuzzable_requests
        
    def _get_to_check( self, target_url ):
        '''
        @param target_url: The url object we can use to extract some information from.
        @return: From the domain, get a list of FQDN, rootDomain and IP address.
        '''
        res = []
        
        addrinfo = None
        try:
            addrinfo = socket.getaddrinfo( target_url.getDomain(), 0)
        except:
            pass
        else:
            res.extend( [info[4][0] for info in addrinfo] )
        
        fqdn = ''
        try:
            fqdn = socket.getfqdn( target_url.getDomain() )
        except:
            pass
        else:
            res.append( fqdn )
            
        try:
            root_domain = target_url.getRootDomain()
        except Exception, e:
            om.out.debug( str(e) )
        else:
            res.append( root_domain )
        
        res = list( set( res ) )
        return res
            
        
    def _is_in_phishtank( self, to_check_list ):
        '''
        Reads the phishtank db and tries to match the entries on that db with the to_check_list
        @return: A list with the sites to match against the phishtank db
        '''
        class phishTankMatch:
            '''
            Represents a phishtank match between the site I'm scanning and
            something in the index.xml file.
            '''
            def __init__( self, url, more_info_URL ):
                self.url = url
                self.more_info_URL = more_info_URL
        
        class phishtankHandler(ContentHandler):
            '''
            <entry>
                <url><![CDATA[http://cbisis.be/.,/www.paypal.com/login/user-information/paypal.support/]]></url>
                <phish_id>118884</phish_id>
                <phish_detail_url><![CDATA[http://www.phishtank.com/phish_detail.php?phish_id=118884]]></phish_detail_url>
                <submission>
                    <submission_time>2007-03-03T21:01:19+00:00</submission_time>
                </submission>
                <verification>
                    <verified>yes</verified>
                    <verification_time>2007-03-04T01:58:05+00:00</verification_time>
                </verification>
                <status>
                    <online>yes</online>
                </status>
            </entry>
            '''
            def __init__ (self, to_check_list):
                self._to_check_list = to_check_list
                self.inside_entry = False
                self.inside_URL = False
                self.inside_detail = False
                self.matches = []
        
            def startElement(self, name, attrs):
                if name == 'entry':
                    self.inside_entry = True
                elif name == 'url':
                    self.inside_URL = True
                    self.url = ""
                elif name == 'phish_detail_url':
                    self.inside_detail = True
                    self.phish_detail_url = ""
                return
            
            def characters (self, ch):
                if self.inside_URL:
                    self.url += ch
                if self.inside_detail:
                    self.phish_detail_url += ch
            
            def endElement(self, name):
                if name == 'phish_detail_url':
                    self.inside_detail = False
                if name == 'url':
                    self.inside_URL = False
                if name == 'entry':
                    self.inside_entry = False
                    #
                    #   Now I try to match the entry with an element in the to_check_list
                    #
                    for target_host in self._to_check_list:
                        if target_host in self.url:
                            phish_url = url_object( self.url )
                            target_host_url = url_object( target_host )
                            
                            if target_host_url.getDomain() == phish_url.getDomain() or \
                            phish_url.getDomain().endswith('.' + target_host_url.getDomain() ):
                            
                                phish_detail_url = url_object( self.phish_detail_url )
                                ptm = phishTankMatch( phish_url, phish_detail_url )
                                self.matches.append( ptm )
        
        file_handler = None
        try:
            file_handler = file( self._phishtank_DB )
        except Exception, e:
            raise w3afException('Failed to open phishtank database file: ' + self._phishtank_DB )
        
        parser = make_parser()   
        curHandler = phishtankHandler( to_check_list )
        parser.setContentHandler( curHandler )
        om.out.debug( 'Starting the phishtank xml parsing. ' )
        
        try:
            parser.parse( file_handler )
        except Exception, e:
            om.out.debug( 'XML parsing error: ' + str(e) )
            raise w3afException('phishtank database file is not a valid XML file.' )
        
        om.out.debug( 'Finished xml parsing. ' )
        
        return curHandler.matches

        
    def setOptions( self, OptionList ):
        self._phishtank_DB = OptionList['dbFile'].getValue()
        self._update_DB = OptionList['updateDB'].getValue()
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        d1 = 'The path to the phishtank database file.'
        o1 = option('dbFile', self._phishtank_DB, d1, 'string')
        
        d2 = 'Update the local phishtank database.'
        h2 = 'If True, the plugin will download the phishtank database'
        h2 += ' from http://www.phishtank.com/ .'
        o2 = option('updateDB', self._update_DB, d2, 'boolean', help=h2)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def _do_update(self):
        '''
        This method is called to update the database.
        '''
        file_handler = None
        try:
            file_handler = open( self._phishtank_DB, 'w' )
        except:
            raise w3afException('Failed to open file: ' + self._phishtank_DB )
        
        msg = 'Updating the phishtank database, this will take some minutes'
        msg += ' ( almost 7MB to download ).'
        om.out.information( msg )
        res = self._urlOpener.GET('http://data.phishtank.com/data/online-valid/')
        om.out.information('Download complete, writing to the database file.')
        
        try:
            file_handler.write( res.getBody() )
            file_handler.close()
        except:
            raise w3afException('Failed to write to file: ' + self._phishtank_DB )
        else:
            return True
        
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
        This plugin searches the domain being tested in the phishtank database.
        If your site is in this database the chances are that you were hacked and your server is now being
        used in phishing attacks.
        
        Two configurable parameters exist:
            - dbFile
            - updateDB
        '''
