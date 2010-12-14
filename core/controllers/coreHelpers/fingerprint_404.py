'''
fingerprint_404.py

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
from __future__ import with_statement

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf

import core.data.parsers.urlParser as urlParser

from core.data.fuzzer.fuzzer import createRandAlpha, createRandAlNum
from core.controllers.w3afException import w3afException, w3afMustStopException
from core.controllers.misc.levenshtein import relative_distance_ge
from core.controllers.misc.lru import LRU

from core.controllers.threads.threadManager import threadManagerObj as tm

import urllib
import thread
import cgi

IS_EQUAL_RATIO = 0.90


class fingerprint_404:
    '''
    Read the 404 page(s) returned by the server.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, uriOpener):
        #
        #   Set the opener, I need it to perform some tests and gain the knowledge about the
        #   server's 404 response bodies.
        #
        self._urlOpener =  uriOpener

        #
        #   Internal variables
        #
        self._already_analyzed = False
        self._404_bodies = []
        self._lock = thread.allocate_lock()
        # it is OK to store 200 here, I'm only storing int as the key, and bool as the value.
        self._is_404_LRU = LRU(200)
        
        #
        #   Here I create a is_404 "singleton" that I use in most plugins.
        #
        global is_404
        is_404 = self.is_404
        #
        #   In the plugins, I'll just do something like "from core.controllers.coreHelpers.fingerprint_404 import is_404"
        #   and then "is_404( response )"
        #

    def is_404(self, http_response):
        '''
        All of my previous versions of is_404 were very complex and tried to struggle with all
        possible cases. The truth is that in most "strange" cases I was failing miserably, so now
        I changed my 404 detection once again, but keeping it as simple as possible.
        
        Also, and because I was trying to cover ALL CASES, I was performing a lot of
        requests in order to cover them, which in most situations was unnecesary.
        
        So now I go for a much simple approach:
            1- Cover the simplest case of all using only 1 HTTP request
            2- Give the users the power to configure the 404 detection by setting a string that
            identifies the 404 response (in case we are missing it for some reason in case #1)
        
        @parameter http_response: The HTTP response which we want to know if it is a 404 or not.
        '''

        #   This is here for testing.
        #return False
        
        #
        #   First we handle the user configured exceptions:
        #
        domain_path = urlParser.getDomainPath(http_response.getURL())
        if domain_path in cf.cf.getData('always404'):
            return True
        elif domain_path in cf.cf.getData('never404'):
            return False        
        
        #
        #   This is the most simple case, we don't even have to think about this.
        #
        #   If there is some custom website that always returns 404 codes, then we are
        #   screwed, but this is open source, and the pentester working on that site can modify
        #   these lines.
        #
        if http_response.getCode() == 404:
            return True
            
        #
        #   The user configured setting. "If this string is in the response, then it is a 404"
        #
        if cf.cf.getData('404string') and cf.cf.getData('404string') in http_response:
            return True
            
        #
        #   Before actually working, I'll check if this response is in the LRU, if it is I just return
        #   the value stored there.
        #
        if http_response.id in self._is_404_LRU:
            return self._is_404_LRU[ http_response.id ]
            
        with self._lock:
            if not self._already_analyzed:
                # Generate a 404 and save it
                self._404_bodies = self._generate_404_knowledge( http_response.getURL() )
                self._already_analyzed = True

        
        # self._404_body was already cleaned inside self._generate_404_knowledge
        # so we need to clean this one.
        html_body = self._get_clean_body( http_response )
        
        #
        #   Compare this response to all the 404's I have in my DB
        #
        for body_404_db in self._404_bodies:
            
            if relative_distance_ge(body_404_db, html_body, IS_EQUAL_RATIO):
                msg = '"%s" is a 404. [similarity_index > %s]' % \
                    (http_response.getURL(), IS_EQUAL_RATIO)
                om.out.debug(msg)
                self._is_404_LRU[ http_response.id ] = True
                return True
            else:
                # If it is not eq to one of the 404 responses I have in my DB, that does not means
                # that it won't match the next one, so I simply do nothing
                pass
        
        else:
            #
            #   I get here when the for ends and no 404 is matched.
            #
            msg = '"%s" is NOT a 404. [similarity_index < %s]' % \
            (http_response.getURL(), IS_EQUAL_RATIO)
            om.out.debug(msg)
            self._is_404_LRU[ http_response.id ] = False
            return False
            
    def _generate_404_knowledge( self, url ):
        '''
        Based on a URL, request something that we know is going to be a 404.
        Afterwards analyze the 404's and summarise them.
        
        @return: A list with 404 bodies.
        '''
        # Get the filename extension and create a 404 for it
        extension = urlParser.getExtension( url )
        domain_path = urlParser.getDomainPath( url )
        
        # the result
        self._response_body_list = []
        
        #
        #   This is a list of the most common handlers, in some configurations, the 404
        #   depends on the handler, so I want to make sure that I catch the 404 for each one
        #
        handlers = ['py', 'php', 'asp', 'aspx', 'do', 'jsp', 'rb', 'do', 'gif', 'htm', extension]
        handlers += ['pl', 'cgi', 'xhtml', 'htmls']
        handlers = list(set(handlers))
        
        for extension in handlers:

            rand_alnum_file = createRandAlNum( 8 ) + '.' + extension
                
            url404 = urlParser.urlJoin(  domain_path , rand_alnum_file )

            #   Send the requests using threads:
            targs = ( url404,  )
            tm.startFunction( target=self._send_404, args=targs , ownerObj=self )
            
        # Wait for all threads to finish sending the requests.
        tm.join( self )
        
        #
        #   I have the bodies in self._response_body_list , but maybe they all look the same, so I'll
        #   filter the ones that look alike.
        #
        result = [ self._response_body_list[0], ]
        for i in self._response_body_list:
            for j in self._response_body_list:
                
                if relative_distance_ge(i, j, IS_EQUAL_RATIO):
                    # They are equal, we are ok with that
                    continue
                else:
                    # They are no equal, this means that we'll have to add this to the list
                    result.append(j)
        
        # I don't need these anymore
        self._response_body_list = None
        
        # And I return the ones I need
        result = list(set(result))
        om.out.debug('The 404 body result database has a lenght of ' + str(len(result)) +'.')
        
        return result

    def _send_404(self, url404):
        '''
        Sends a GET request to url404 and saves the response in self._response_body_list .
        @return: None.
        '''
        try:
            # I don't use the cache, because the URLs are random and the only thing that
            # useCache does is to fill up disk space
            response = self._urlOpener.GET(url404, useCache=False, grepResult=False)
        except w3afException, w3:
            raise w3afException('Exception while fetching a 404 page, error: ' + str(w3))
        except w3afMustStopException, mse:
            # Someone else will raise this exception and handle it as expected
            # whenever the next call to GET is done
            raise w3afException('w3afMustStopException <%s> found by _send_404,' \
                                ' someone else will handle it.' % mse)
        except Exception, e:
            om.out.error('Unhandled exception while fetching a 404 page, error: ' + str(e))
            raise

        else:
            # I don't want the random file name to affect the 404, so I replace it with a blank space
            response_body = self._get_clean_body(response)

            self._response_body_list.append(response_body)
        
    #
    #
    #       Some helper functions
    #
    #
    def _get_clean_body(self, response):
        '''
        Definition of clean in this method:
            - input:
                - response.getURL() == http://host.tld/aaaaaaa/
                - response.getBody() == 'spam aaaaaaa eggs'
                
            - output:
                - self._clean_body( response ) == 'spam  eggs'
        
        The same works with filenames.
        All of them, are removed encoded and "as is".
        
        @parameter response: The httpResponse object to clean
        @return: A string that represents the "cleaned" response body of the response.
        '''
        original_body = response.getBody()
        url = response.getURL()
        to_replace = url.split('/')
        to_replace.append( url )
        
        for i in to_replace:
            if len(i) > 6:
                original_body = original_body.replace(i, '')
                original_body = original_body.replace(urllib.unquote_plus(i), '')
                original_body = original_body.replace(cgi.escape(i), '')
                original_body = original_body.replace(cgi.escape(urllib.unquote_plus(i)), '')

        return original_body


