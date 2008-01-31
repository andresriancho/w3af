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
import core.data.constants.severity as severity

class phishtank(baseDiscoveryPlugin):
    '''
    Search the phishtank.com database to determine if your server is (or was) being used in phishing scams.
    
    @author: Andres Riancho ( andres.riancho@gmail.com ) ; special thanks to http://www.phishtank.com/ !
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._run = True
        
        # User defines variable
        self._phishtankDB = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'phishtank' + os.path.sep + 'index.xml'
        self._updateDB = False
        
    def discover(self, fuzzableRequest ):
        self._fuzzableRequests = []
        
        if not self._run:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # Run one time
            self._run = False
            
            if self._updateDB:
                self._doUpdate()
            
            domain = getDomain( fuzzableRequest.getURL() )
            toCheckList = self._getToCheck( domain )
            
            phishTankMatches = self._isInPhishtank( toCheckList )
            for ptm in phishTankMatches:
                response = self._urlOpener.GET( ptm.url )
                self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
                
                v = vuln.vuln()
                v.setURL( ptm.url )
                v.setId( response.id )
                v.setName( 'Phishing scam' )
                v.setSeverity(severity.LOW)
                v.setDesc( ptm.url + ' seems to be involved in a phishing scam. Please see ' + ptm.moreInfoURL + ' for more info.' )
                kb.kb.append( self, 'phishtank', v )
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
            
        
    def _isInPhishtank( self, toCheckList ):
        '''
        Reads the phishtank db and tries to match the entries on that db with the toCheckList
        @return: A list with the sites to match against the phishtank db
        '''
        class phishTankMatch:
            def __init__( self, url, moreInfoURL ):
                self.url = url
                self.moreInfoURL = moreInfoURL
        
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
            def __init__ (self, toCheckList):
                self._toCheckList= toCheckList;
                self.insideEntry = False
                self.insideURL = False
                self.insideDetail = False
                self.matches = []
        
            def startElement(self, name, attrs):
                if name == 'entry':
                        self.insideEntry = True
                elif name == 'url':
                        self.insideURL= True;
                        self.url = "";
                elif name == 'phish_detail_url':
                        self.insideDetail = True;
                        self.phish_detail_url = "";
                return
            
            def characters (self, ch):
                if self.insideURL:
                        self.url += ch
                if self.insideDetail:
                        self.phish_detail_url += ch
            
            def endElement(self, name):
                if name == 'phish_detail_url':
                        self.insideDetail = False
                if name == 'url':
                        self.insideURL = False
                if name == 'entry':
                        self.insideEntry = False
                        #
                        #   Now I try to match the entry with an element in the toCheckList
                        #
                        phishDomain = getDomain( self.url )
                        for url in self._toCheckList:
                            if url == phishDomain or phishDomain.endswith('.' + url ):
                                ptm = phishTankMatch( self.url, self.phish_detail_url )
                                self.matches.append( ptm )
        
        fd = None
        try:
            fd = file( self._phishtankDB )
        except Exception, e:
            raise w3afException('Failed to open phishtank database file: ' + self._phishtankDB )
        
        parser = make_parser()   
        curHandler = phishtankHandler( toCheckList )
        parser.setContentHandler( curHandler )
        om.out.debug( 'Starting the phishtank xml parsing. ' )
        
        try:
            parser.parse( fd )
        except Exception, e:
            om.out.debug( 'XML parsing error: ' + str(e) )
            raise w3afException('phishtank database file is not a valid XML file.' )
        
        om.out.debug( 'Finished xml parsing. ' )
        
        return curHandler.matches

        
    def setOptions( self, OptionList ):
        if 'dbFile' in OptionList.keys(): 
            self._phishtankDB = OptionList['dbFile']
            
        if 'updateDB' in OptionList.keys(): 
            self._updateDB = OptionList['updateDB']
            
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="dbFile">\
                <default>' + self._phishtankDB +'</default>\
                <desc>The path to the phishtank database file.</desc>\
                <type>string</type>\
                <help>The default is ok in most cases.</help>\
            </Option>\
            <Option name="updateDB">\
                <default>'+str(self._updateDB)+'</default>\
                <desc>Update the local phishtank database.</desc>\
                <type>boolean</type>\
                <help>If True, the plugin will download the phishtank database from http://www.phishtank.com/ .</help>\
            </Option>\
        </OptionList>\
        '

    def _doUpdate(self):
        '''
        This method is called to update the database.
        '''
        fd = None
        try:
            fd = open( self._phishtankDB, 'w' )
        except:
            raise w3afException('Failed to open file: ' + self._phishtankDB )
            
        om.out.information('Updating the phishtank database, this will take some minutes ( almost 7MB to download ).')
        res = self._urlOpener.GET('http://data.phishtank.com/data/online-valid/')
        om.out.information('Download complete, writing to the database file.')
        
        try:
            fd.write( res.getBody() )
            fd.close()
        except:
            raise w3afException('Failed to write to file: ' + self._phishtankDB )
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
