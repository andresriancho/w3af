# coding: utf8
'''
sgmlParser.py

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

import re
import traceback

from lxml import etree

from core.data.parsers.baseparser import BaseParser
from core.data.parsers.urlParser import url_object
import core.controllers.outputManager as om


class SGMLParser(BaseParser):
    '''
    The target SAX-like SGML parser. Methods 'start', 'end', 'data', 'comment'
    and 'close' will be called during the parsing process. 
    
    @author: Javier Andalia (jandalia =at= gmail.com)
             Andres Riancho (andres.riancho@gmail.com)
    '''
    
    TAGS_WITH_URLS = (
        'go', 'a', 'anchor', 'img', 'link', 'script', 'iframe', 'object',
        'embed', 'area', 'frame', 'applet', 'input', 'base', 'div', 'layer',
        'form', 'ilayer', 'bgsound', 'html', 'audio', 'video'
        )
    
    URL_ATTRS = ('href', 'src', 'data', 'action', 'manifest')

    # I don't want to inject into Apache's directory indexing parameters
    APACHE_INDEXING = ("?C=N;O=A", "?C=M;O=A", "?C=S;O=A", "?C=D;O=D",
                       '?C=N;O=D', '?C=D;O=A', '?N=D', '?M=A', '?S=A',
                       '?D=A', '?D=D', '?S=D', '?M=D', '?N=D')
    
    def __init__(self, http_resp):
        BaseParser.__init__(self, http_resp)
        
        # Internal state variables
        self._inside_form = False
        self._inside_select = False
        self._inside_textarea = False
        self._inside_script = False
        
        # Internal containers
        self._tag_and_url = set()
        self._parsed_urls = set()
        self._forms = []
        self._comments_in_doc = []
        self._scripts_in_doc = []
        self._meta_redirs = []
        self._meta_tags = []
        
        # Do some stuff before actually parsing
        self._pre_parse(http_resp)
        
        # Parse!
        self._parse(http_resp)
    
    def start(self, tag, attrs):
        '''
        Called by the parser on element open.
        '''
        try:
            # Call start_tag handler method
            meth = getattr(self, '_handle_'+ tag +'_tag_start',
                           lambda *args: None)
            meth(tag, attrs)
            
            if tag in self.TAGS_WITH_URLS:
                self._find_references(tag, attrs)
        except Exception, ex:
            msg = 'An exception occurred while parsing a document: %s' % ex
            om.out.error(msg)
            om.out.error('Error traceback: %s' % traceback.format_exc())
    
    def end(self, tag):
        '''
        Called by the parser on element close.
        '''
        # Call handler method if exists
        getattr(self, '_handle_'+ tag +'_tag_end', lambda arg: None)(tag)
        
    
    def data(self, data):
        '''
        Called by the parser when a text node is found.
        '''
        pass
    
    def comment(self, text):
        if self._inside_script:
            self._scripts_in_doc.append(text)
        else:
            self._comments_in_doc.append(text)
    
    def close(self):
        pass
    
    def _pre_parse(self, http_resp):
        '''
        Perform some initialization tasks
        '''
        body = http_resp.body
        self._regex_url_parse(body)
        self._findEmails(body)
    
    def _parse(self, http_resp):
        '''
        Parse the response.
        '''
        # Start parsing!
        parser = etree.HTMLParser(target=self, recover=True)
        resp_body = http_resp.body
        try:
            etree.fromstring(resp_body, parser)
        except ValueError:
            # Sometimes we get XMLs in the response. lxml fails to parse them
            # when an encoding header is specified and the text is unicode. So
            # we better make an exception and convert it to string. Note that
            # yet the parsed elems will be unicode.
            resp_body = resp_body.encode(
                                     http_resp.charset, 'xmlcharrefreplace')
            parser = etree.HTMLParser(
                                target=self,
                                recover=True,
                                encoding=http_resp.charset,
                            )
            etree.fromstring(resp_body, parser)
        except etree.XMLSyntaxError:
            msg = 'An error occurred while parsing "%s", original exception: "%s"'
            msg = msg % (http_resp.getURL(), etree.XMLSyntaxError)
            om.out.debug(msg)

    def _filter_ref(self, attr):
        key = attr[0]
        value = attr[1]
        
        return  key in self.URL_ATTRS and value \
                and not value.startswith('#') \
                and not value in self.APACHE_INDEXING
 
    def _find_references(self, tag, attrs):
        '''
        Find references inside the document.
        '''
        
        filter_ref = self._filter_ref
        
        for _, url_path in filter(filter_ref, attrs.iteritems()):
            try:
                url_path = self._decode_url(url_path)
                url = unicode(self._baseUrl.urlJoin(url_path))
                url = url_object(url, encoding=self._encoding)
            except ValueError:
                # Just ignore it, this happens in many cases but one
                # of the most noticeable is "d:url.html", where the 
                # developer uses a colon in the URL.
                msg = 'Ignoring URL "%s" as it generated an invalid URL.'
                om.out.debug( msg % url_path)
            else:
                url.normalizeURL()
                # Save url
                self._parsed_urls.add(url)
                self._tag_and_url.add((tag, url))
        
    def _fill_forms(self, tag, attrs):
        raise NotImplementedError('This method must be overriden by a subclass')
    
    
    ## Properties ##
    
    @property
    def forms(self):
        '''
        @return: Return list of forms.
        '''
        return self._forms        

    def getForms(self):
        return self.forms
    
    @property
    def references(self):
        '''
        Searches for references on a page. w3af searches references in every
        html tag, including "a", "forms", "images", "frames", etc.
        
        Return a tuple containing two sets, one with the parsed URLs, and the
        other with the URLs that came out from a regular expression. The 
        second list is less trustworthy.
        '''
        return (list(self._parsed_urls), list(self._re_urls-self._parsed_urls))
        
    def getReferences(self):
        return self.references
    
    @property
    def comments(self):
        '''
        Return list of comment strings.
        '''
        return set(self._comments_in_doc)

    def getComments(self):
        return self.comments
    
    @property
    def scripts(self):
        '''
        Return list of scripts (mainly javascript, but can be anything)
        '''
        return set(self._scripts_in_doc)
    
    def getScripts(self):
        return self.scripts
    
    @property
    def meta_redirs(self):
        '''
        Return list of meta redirections.
        '''
        return self._meta_redirs
        
    def getMetaRedir(self):
        return self.meta_redirs
    
    @property
    def meta_tags(self):
        '''
        Return list of all meta tags.
        '''
        return self._meta_tags
    
    def getMetaTags(self):
        return self.meta_tags
        
    def getReferencesOfTag(self, tagType):
        '''
        @return: A list of the URLs that the parser found in a tag of
            tagType = "tagType" (i.e img, a)
        '''
        return [x[1] for x in self._tag_and_url if x[0] == tagType]
    
    
    ## Methods for tags handling ##

    def _handle_base_tag_start(self, tag, attrs):
        # Override base url
        try:
            self._baseUrl = self._baseUrl.urlJoin(attrs.get('href', ''))
        except ValueError:
            pass
    
    def _handle_meta_tag_start(self, tag, attrs):
        self._meta_tags.append(attrs.items())
        
        has_HTTP_EQUIV = attrs.get('http-equiv', '') == 'refresh'
        content = attrs.get('content', None)
                
        if content is not None and has_HTTP_EQUIV:
            self._meta_redirs.append(content)
            
            # Finally add the URL to the list of urls found in the document.
            # The content variables may look like:
            #   "4;URL=http://www.f00.us/"
            #   "2; URL=http://www.f00.us/"
            #   "6  ; URL=http://www.f00.us/"
            for urlstr in re.findall('.*?URL.*?=(.*)', content, re.IGNORECASE):
                urlstr = self._decode_url(urlstr.strip())
                url = unicode(self._baseUrl.urlJoin(urlstr))
                url = url_object(url, encoding=self._encoding) 
                self._parsed_urls.add(url)
                self._tag_and_url.add(('meta', url))

    def _handle_form_tag_start(self, tag, attrs):
        self._inside_form = True

    def _handle_form_tag_end(self, tag):
        self._inside_form = False

    def _handle_script_tag_start(self, tag, attrs):
        self._inside_script = True
    
    def _handle_script_tag_end(self, tag):
        self._inside_script = False
    
    def _handle_select_tag_start(self, tag, attrs):
        self._inside_select = True
    
    def _handle_select_tag_end(self, tag):
        self._inside_select = False
    
    def _handle_textarea_tag_start(self, tag, attrs):
        self._inside_textarea = True
    
    def _handle_textarea_tag_end(self, tag):
        self._inside_textarea = False
    