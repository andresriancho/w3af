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
import codecs
import os.path
import socket

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.data.options.opt_factory import opt_factory
from core.data.options.option_types import INPUT_FILE, BOOL
from core.data.options.option_list import OptionList
from core.data.parsers.url import URL

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afRunOnce, w3afException
from core.controllers.misc.decorators import runonce


class phishtank(CrawlPlugin):
    '''
    Search the phishtank.com database to determine if your server is (or was)
    being used in phishing scams.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    @author: Special thanks to http://www.phishtank.com/ !
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)

        # User defines variable
        self._phishtank_DB = os.path.join('plugins', 'crawl', 'phishtank',
                                          'index.xml')
        self._update_DB = False
    
    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request ):
        '''
        Plugin entry point, perform all the work.
        '''
        if self._update_DB:
            self._do_update()
        
        to_check = self._get_to_check( fuzzable_request.getURL() )
        
        # I found some URLs, create fuzzable requests
        phishtank_matches = self._is_in_phishtank( to_check )
        for ptm in phishtank_matches:
            response = self._uri_opener.GET( ptm.url )
            for fr in self._create_fuzzable_requests( response ):
                self.output_queue.put(fr)
        
        # Only create the vuln object once
        if phishtank_matches:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.setURL( ptm.url )
            v.set_id( response.id )
            v.set_name( 'Phishing scam' )
            v.set_severity(severity.MEDIUM)
            desc = 'The URL: "%s" seems to be involved in a phishing scam.' \
                   ' Please see %s for more info.'
            v.set_desc(desc % (ptm.url, ptm.more_info_URL))
            kb.kb.append( self, 'phishtank', v )
            om.out.vulnerability( v.get_desc(), severity=v.get_severity() )
        
    def _get_to_check( self, target_url ):
        '''
        @param target_url: The url object we can use to extract some information.
        @return: From the domain, get a list of FQDN, rootDomain and IP address.
        '''
        def addrinfo(url):
            return [x[4][0] for x in socket.getaddrinfo(url.getDomain(), 0)]
        
        def getfqdn(url):
            return [socket.getfqdn(url.getDomain()),]
        
        def root_domain(url):
            return [url.getRootDomain(),]
        
        res = set()
        for func in (addrinfo, getfqdn, root_domain):
            try:
                data_lst = func(target_url)
            except Exception:
                pass
            else:
                for data in data_lst:
                    res.add(data)
        
        return res
        
    def _is_in_phishtank(self, to_check):
        '''
        Reads the phishtank db and tries to match the entries on that db with
        the to_check
        
        @return: A list with the sites to match against the phishtank db
        '''
        class PhishTankMatch(object):
            '''
            Represents a phishtank match between the site I'm scanning and
            something in the index.xml file.
            '''
            def __init__( self, url, more_info_URL ):
                self.url = url
                self.more_info_URL = more_info_URL
        
        class PhishTankHandler(ContentHandler):
            '''
            <entry>
                <url><![CDATA[http://cbisis...paypal.support/]]></url>
                <phish_id>118884</phish_id>
                <phish_detail_url>
                    <![CDATA[http://www.phishtank.com/phish_detail.php?phish_id=118884]]>
                </phish_detail_url>
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
            def __init__ (self, to_check):
                self._to_check = to_check
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
            
            def characters(self, ch):
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
                    #    Now I try to match the entry with an element in the
                    #    to_check_list
                    #
                    for target_host in self._to_check:
                        if target_host in self.url:
                            phish_url = URL( self.url )
                            target_host_url = URL( target_host )
                            
                            if target_host_url.getDomain() == phish_url.getDomain() or \
                            phish_url.getDomain().endswith('.' + target_host_url.getDomain() ):
                            
                                phish_detail_url = URL( self.phish_detail_url )
                                ptm = PhishTankMatch( phish_url, phish_detail_url )
                                self.matches.append( ptm )
        
        try:
            phishtank_db_fd = codecs.open(self._phishtank_DB, 'r', 'utf-8',
                                          errors='ignore')
        except Exception, e:
            msg = 'Failed to open phishtank database file: "%s", exception: "%s".'
            raise w3afException(msg % (self._phishtank_DB, e))
        
        parser = make_parser()   
        pt_handler = PhishTankHandler(to_check)
        parser.setContentHandler( pt_handler )
        om.out.debug( 'Starting the phishtank xml parsing. ' )
        
        try:
            parser.parse( phishtank_db_fd )
        except Exception, e:
            msg = 'XML parsing error in phishtank DB, exception: "%s".'
            raise w3afException(msg % e)
        
        om.out.debug( 'Finished xml parsing. ' )
        
        return pt_handler.matches

    def set_options( self, option_list ):
        self._phishtank_DB = option_list['db_file'].get_value()
        self._update_DB = option_list['update_db'].get_value()
    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = OptionList()
        
        d = 'The path to the phishtank database file.'
        o = opt_factory('db_file', self._phishtank_DB, d, INPUT_FILE)
        ol.add(o)
        
        d = 'Update the local phishtank database.'
        h = 'If True, the plugin will download the phishtank database'\
            ' from http://www.phishtank.com/ .'
        o = opt_factory('update_db', self._update_DB, d, BOOL, help=h)
        ol.add(o)
        
        return ol

    def _do_update(self):
        '''
        This method is called to update the database.
        '''
        try:
            file_handler = codecs.open( self._phishtank_DB, 'w', 'utf-8' )
        except Exception, e:
            msg = 'Failed to open file: "%s", error: "%s".'
            raise w3afException(msg % (self._phishtank_DB,e))
        
        msg = 'Updating the phishtank database, this will take some minutes'\
              ' ( almost 7MB to download ).'
        om.out.information( msg )
        
        update_url = URL('http://data.phishtank.com/data/online-valid/')
        res = self._uri_opener.GET( update_url )
        om.out.information('Download complete, writing to the database file.')
        
        try:
            file_handler.write(res.getBody())
            file_handler.close()
        except Exception, e:
            msg = 'Failed to write to file: "%s", error: "%s".'
            raise w3afException(msg % (self._phishtank_DB,e))
        else:
            return True
        
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches the domain being tested in the phishtank database.
        If your site is in this database the chances are that you were hacked
        and your server is now being used in phishing attacks.
        
        Two configurable parameters exist:
            - db_file
            - update_db
        '''
