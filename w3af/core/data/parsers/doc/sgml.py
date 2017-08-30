# coding: utf8
"""
sgml.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import urllib
import re
import traceback
import StringIO

from lxml import etree
from collections import namedtuple

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.misc_settings import EXCLUDE, INCLUDE
from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.controllers.exceptions import ParserException


Tag = namedtuple('Tag', ('name', 'attrib', 'text'))


class SGMLParser(BaseParser):
    """
    The target SAX-like SGML parser. Methods 'start', 'end', 'data', 'comment'
    and 'close' will be called during the parsing process.

    :author: Javier Andalia (jandalia =at= gmail.com)
             Andres Riancho (andres.riancho@gmail.com)
    """
    ANY_TAG_MATCH = re.compile('(<.*?>)', re.UNICODE)

    EMAIL_RE = re.compile(
        '([\w\.%-]{1,45}@([A-Z0-9\.-]{1,45}\.){1,10}[A-Z]{2,4})',
        re.I | re.U)

    META_URL_REDIR_RE = re.compile('.*?URL.*?=(.*)', re.I | re.U)

    TAGS_WITH_URLS = {
        'go', 'a', 'anchor', 'img', 'link', 'script', 'iframe', 'object',
        'embed', 'area', 'frame', 'applet', 'input', 'base', 'div', 'layer',
        'form', 'ilayer', 'bgsound', 'html', 'audio', 'video'
    }

    URL_ATTRS = {'href', 'src', 'data', 'action', 'manifest', 'link', 'uri'}

    # Configure which tags will be analyzed by the parser
    PARSE_TAGS = TAGS_WITH_URLS.union({'meta'})

    # I don't want to inject into Apache's directory indexing parameters
    APACHE_INDEXING = {"?C=N;O=A", "?C=M;O=A", "?C=S;O=A", "?C=D;O=D",
                       '?C=N;O=D', '?C=D;O=A', '?N=D', '?M=A', '?S=A',
                       '?D=A', '?D=D', '?S=D', '?M=D', '?N=D'}

    def __init__(self, http_resp):
        BaseParser.__init__(self, http_resp)

        # Internal state variables
        self._inside_form = False
        self._inside_select = False
        self._inside_text_area = False
        self._inside_script = False

        self._tag_and_url = set()
        self._forms = []
        self._comments_in_doc = []
        self._meta_redirs = []
        self._meta_tags = []
        self._emails = set()

    def clear(self):
        super(SGMLParser, self).clear()

        # Internal containers
        self._tag_and_url.clear()
        self._forms = []
        self._comments_in_doc = []
        self._meta_redirs = []
        self._meta_tags = []
        self._emails.clear()

    def _handle_exception(self, where, ex):
        msg = 'An exception occurred while %s: "%s"'
        om.out.error(msg % (where, ex))
        om.out.error('Error traceback: %s' % traceback.format_exc())

    def start(self, tag):
        """
        Called by the parser on element open.
        """
        # Get the important info
        attrs = dict(tag.attrib)
        tag_name = tag.tag

        # Call start_tag handler method
        handler = '_handle_%s_tag_start' % tag_name

        try:
            method = getattr(self, handler)
        except AttributeError:
            pass
        else:
            try:
                method(tag, tag_name, attrs)
            except Exception, ex:
                self._handle_exception('parsing %s tag' % tag_name, ex)

        try:
            if tag_name in self.TAGS_WITH_URLS:
                self._find_references(tag, tag_name, attrs)
        except Exception, ex:
            self._handle_exception('extracting references', ex)

        try:
            # Before I defined TAGS_WITH_MAILTO = {'a'} at the class level, but
            # since it had only one item, and this doesn't change often (ever?)
            # changed it to this for performance
            if tag_name == 'a':
                self._find_emails(tag, tag_name, attrs)
        except Exception, ex:
            self._handle_exception('finding emails', ex)

    def end(self, tag):
        """
        Called by the parser on element close.
        """
        # Call handler method if exists
        try:
            method = getattr(self, '_handle_%s_tag_end' % tag.tag)
        except AttributeError:
            return
        else:
            return method(tag)

    def comment(self, elem):
        if self._inside_script:
            # This handles the case where we have:
            # <script><!-- code(); --></script>
            return

        if elem.text is not None:
            self._comments_in_doc.append(smart_unicode(elem.text))

    def close(self):
        pass

    def parse(self):
        """
        Parse the HTTP response body
        """
        http_resp = self.get_http_response()
        resp_body = http_resp.get_body()

        try:
            self._parse_response_body_as_string(resp_body, errors='ignore')
        except etree.XMLSyntaxError, xse:
            #
            # This is too common, we don't want to raise an exception because
            # of invalid / broken HTML
            #
            msg = 'Error occurred while parsing "%s", original exception: "%s"'
            om.out.debug(msg % (http_resp.get_url(), xse))

    def _parse_response_body_as_string(self, resp_body, errors='strict'):
        """
        Parse the HTTP response body
        """
        # HTML Parser raises XMLSyntaxError on empty response body #8695
        # https://github.com/andresriancho/w3af/issues/8695
        if not resp_body:
            # Simply return, don't even try to parse this response, it's empty
            # anyways. The result of this return is to have an empty SGMLParser
            # which won't have any links, forms, etc. (correct for a response
            # body which is empty).
            return

        resp_body = resp_body.encode(DEFAULT_ENCODING, errors=errors)
        body_io = StringIO.StringIO(resp_body)
        event_map = {'start': self.start,
                     'end': self.end,
                     'comment': self.comment}

        # Performance notes:
        #
        #   * recover=True doesn't have any impact on memory usage
        #
        #   * huge_tree=False is related with security, if there is a huge tree
        #     lxml will refuse to parse it, and that's OK
        #
        #   * tag=self.PARSE_TAGS makes sure that we only go to python code when
        #     strictly required (CPU usage reduction)
        context = etree.iterparse(body_io,
                                  events=event_map.keys(),
                                  tag=self.PARSE_TAGS,
                                  html=True,
                                  recover=True,
                                  encoding=DEFAULT_ENCODING,
                                  huge_tree=False)

        for event, elem in context:
            try:
                event_map[event](elem)
            except Exception, e:
                msg = ('Found a parser exception while handling tag "%s" with'
                       ' event "%s". The exception was: "%s"')
                args = (elem.tag, event, e)
                raise ParserException(msg % args)

            # Memory usage improvements notes:
            #
            #   * These lines actually make a difference, they reduce memory
            #     usage from ~270MB to ~230MB when parsing a huge HTML document
            #
            # But... these lines also create a horrible monster:
            #
            #   ***
            #   Error in `python': malloc(): memory corruption (fast):
            #   0x00007f13a40d5f70
            #   ***
            #
            # Which is 100% related to the lines below, so I better remove them
            # leaving the comment as a reminder to future devs which want to
            # improve the parser's memory usage
            #
            # Maybe with a future version of lxml this doesn't happen?
            # Comment date: 26 May 2015
            """
            elem.clear()
            while elem.getprevious() is not None:
                try:
                    del elem.getparent()[0]
                except TypeError:
                    # TypeError: 'NoneType' object does not support item deletion
                    # Happens when elem.getparent() returns None
                    pass
            """

        # Memory usage reduction
        del context

        # This was called when using etree.fromstring, and I used it so
        # let's keep calling it
        self.close()

    def get_tags_by_filter(self, tags, yield_text=False):
        """
        :param tags: A tuple with the tag names to yield. Use None if you want
                     all tags to be returned.

        :return: Yield tuples with (tag_name, tag_attrs, tag_text)

        :see: https://github.com/andresriancho/w3af/issues/9990
        :see: _parse_response_body_as_string for more/better docs
        """
        resp_body = self.get_http_response().body

        # HTML Parser raises XMLSyntaxError on empty response body #8695
        # https://github.com/andresriancho/w3af/issues/8695
        if not resp_body:
            # Don't even try to parse this response, it's empty anyways.
            raise StopIteration

        body_io = StringIO.StringIO(resp_body.encode(DEFAULT_ENCODING))

        # Performance notes, see "_parse_response_body_as_string"
        context = etree.iterparse(body_io,
                                  events=('start',),
                                  tag=tags,
                                  html=True,
                                  recover=True,
                                  encoding=DEFAULT_ENCODING,
                                  huge_tree=False)

        for event, elem in context:

            # We do this to save some memory
            text = None
            if yield_text:
                text = elem.text

            yield Tag(elem.tag, dict(elem.attrib), text)

            # Performance notes, see "_parse_response_body_as_string"
            """
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            """

        # Memory usage reduction
        del context

    def get_emails(self, domain=None):
        """
        :param domain: Indicates what email addresses I want to retrieve.
                       All are returned if the domain is not set.

        :return: A list of email accounts that are inside the document.
        """
        if domain:
            return [i for i in self._emails if domain == i.split('@')[1]]
        else:
            return self._emails

    def _find_emails(self, tag, tag_name, attrs):
        """
        Extract "mailto:" email addresses

        :param tag_name: The tag which is being parsed
        :param attrs: The attributes for that tag
        :return: Store the emails in self._emails
        """
        for key, mailto_address in attrs.iteritems():
            if key not in self.URL_ATTRS:
                continue

            if '@' not in mailto_address:
                continue

            if mailto_address.lower().startswith('mailto:'):
                try:
                    email = self._parse_mailto(mailto_address)
                except ValueError:
                    # It was an invalid email
                    pass
                else:
                    self._emails.add(email)

    def _parse_mailto(self, mailto):
        mailto = urllib.unquote_plus(mailto)
        colon_split = mailto.split(':', 1)
        quest_split = colon_split[1].split('?', 1)
        email = quest_split[0].strip()
        if self.EMAIL_RE.match(email):
            return email
        else:
            raise ValueError('Invalid email address "%s"' % email)

    def _filter_ref(self, attr):
        """
        :param attr: An attribute key/value
        :return: True if the attribute value is a valid link
        """
        key = attr[0]
        value = attr[1]

        return (value
                and key in self.URL_ATTRS
                and not value.startswith('#')
                and not value.startswith('tel:')
                and not value.startswith('callto:')
                and not value.startswith('mailto:')
                and not value in self.APACHE_INDEXING)

    def _find_references(self, tag, tag_name, attrs):
        """
        Find references inside the document.
        """
        filter_ref = self._filter_ref
        base_url = self._base_url
        decode_url = self._decode_url

        for _, url_path in filter(filter_ref, attrs.iteritems()):
            try:
                url_path = decode_url(url_path)
                url = base_url.url_join(url_path, encoding=self._encoding)
            except ValueError:
                # Just ignore it, this happens in many cases but one
                # of the most noticeable is "d:url.html", where the
                # developer uses a colon in the URL.
                msg = 'Ignoring URL "%s" as it generated an invalid URL.'
                om.out.debug(msg % url_path)
            else:
                # The url_join call already normalizes the URL, there is no
                # need to call normalize again
                # url.normalize_url()

                # Save url
                self._tag_and_url.add((tag_name, url))

    #
    # Properties
    #
    @property
    def forms(self):
        """
        :return: Return list of forms filtered using the form_id_list and
                 form_id_action user configuration settings.
        """
        form_id_list = cf.cf.get('form_id_list')
        form_id_action = cf.cf.get('form_id_action') or EXCLUDE

        if form_id_list is not None and len(form_id_list.get_form_ids()):
            filtered_forms = []

            for form in self._forms:
                form_id = form.get_form_id()
                matches_one_config_filter = form_id.matches_one_of(form_id_list)

                if matches_one_config_filter and form_id_action == INCLUDE:
                    filtered_forms.append(form)
                elif not matches_one_config_filter and form_id_action == EXCLUDE:
                    filtered_forms.append(form)

            return filtered_forms

        return self._forms

    def get_forms(self):
        return self.forms

    @property
    def references(self):
        """
        Searches for references on a page. w3af searches references in every
        html tag, including "a", "forms", "images", "frames", etc.

        Return a tuple containing two sets, one with the parsed URLs, and the
        other with the URLs that came out from a regular expression. The
        second list is less trustworthy.
        """
        return [url for tag, url in self._tag_and_url], []

    def get_references(self):
        return self.references

    @property
    def comments(self):
        """
        Return list of comment strings.
        """
        return set(self._comments_in_doc)

    def get_comments(self):
        return self.comments

    @property
    def meta_redirs(self):
        """
        Return list of meta redirections.
        """
        return self._meta_redirs

    def get_meta_redir(self):
        return self.meta_redirs

    @property
    def meta_tags(self):
        """
        Return list of all meta tags.
        """
        return self._meta_tags

    def get_meta_tags(self):
        return self.meta_tags

    def get_clear_text_body(self):
        """
        :return: A clear text representation of the HTTP response body.
        """
        body = self.get_http_response().get_body()
        clear_text = self.ANY_TAG_MATCH.sub(u'', body)
        return clear_text

    def get_references_of_tag(self, tag_type):
        """
        :return: A list of the URLs that the parser found in a tag of
            tagType = "tagType" (i.e img, a)
        """
        return [x[1] for x in self._tag_and_url if x[0] == tag_type]

    ## Methods for tags handling ##
    def _handle_base_tag_start(self, tag, tag_name, attrs):
        # Override base url
        try:
            self._base_url = self._base_url.url_join(attrs.get('href', ''))
        except ValueError:
            pass

    def _handle_meta_tag_start(self, tag, tag_name, attrs):
        self._meta_tags.append(attrs)

        has_HTTP_EQUIV = attrs.get('http-equiv', '') == 'refresh'
        content = attrs.get('content', None)

        if content is not None and has_HTTP_EQUIV:
            self._meta_redirs.append(content)

            # Finally add the URL to the list of urls found in the document.
            # The content variables may look like:
            #   "4;URL=http://www.f00.us/"
            #   "2; URL=http://www.f00.us/"
            #   "6  ; URL=http://www.f00.us/"
            for urlstr in self.META_URL_REDIR_RE.findall(content):
                urlstr = self._decode_url(urlstr.strip())
                url = unicode(self._base_url.url_join(urlstr))
                url = URL(url, encoding=self._encoding)
                self._tag_and_url.add(('meta', url))

    def _handle_form_tag_start(self, tag, tag_name, attrs):
        self._inside_form = True

    def _handle_form_tag_end(self, tag):
        self._inside_form = False

    def _handle_script_tag_start(self, tag, tag_name, attrs):
        self._inside_script = True

    def _handle_script_tag_end(self, tag):
        self._inside_script = False

    def _handle_select_tag_start(self, tag, tag_name, attrs):
        self._inside_select = True

    def _handle_select_tag_end(self, tag):
        self._inside_select = False

    def _handle_textarea_tag_start(self, tag, tag_name, attrs):
        self._inside_text_area = True

    def _handle_textarea_tag_end(self, tag):
        self._inside_text_area = False
