"""
websockets_links.py

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
import re

from lxml import etree

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.parsers.doc.javascript import JavaScriptParser
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.kb.info import Info
import w3af.core.controllers.output_manager as om


WS_URL = "ws://"
WSS_URL = "wss://"
WEBSOCKETS_URL_RE = re.compile('["|\']{1}wss?:\/\/'
                               '[\da-z\.-]+'
                               '(\.[a-z\.]{2,6})?'
                               '(\:\d{1,5})?'
                               '([\da-z\.-\_\/])*["|\']{1}', re.U | re.I)
SCRIPT_TAG_XPATH = "//script"


def find_websockets_links(text):
    ws_links = set()
    mobjects = WEBSOCKETS_URL_RE.finditer(text)
    for ws_mo in mobjects:
        try:
            ws_links.add(ws_mo.group(0))
        except ValueError:
            pass
    return ws_links


class websockets_links(GrepPlugin):
    """
    Finds ws:// or wss:// links within html or javascript docs.

    :author: Dmitry Roshchin (nixwizard@gmail.com)
    """
    def grep(self, request, response):
        """
        websockets_links

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        # if it is not html or js we are not interested
        if not response.is_text_or_html():
            return

        # checking if websockets are in use the fast way and if they
        # are moving on to slower checks
        if not (WS_URL in response.body or WSS_URL in response.body):
            return

        # if websockets usage signs were found we need to get the exact url
        url = request.get_url()

        # if it is javascript we search the whole doc
        if JavaScriptParser(response).can_parse(response):
            ws_links = find_websockets_links(response.body)
        else:
            # if it is html we should search inside <script> tags only
            dom = response.get_dom()

            if dom is None:
                return

            ws_links = set()
            script_tag_xpath = etree.XPath(SCRIPT_TAG_XPATH)

            for script in script_tag_xpath(dom):
                for ws_link in find_websockets_links(script.text):
                    ws_links.add(ws_link)

        # if we didn't find any link manual inspection is needed
        if len(ws_links) == 0:
            # TODO: In some scenarios this message is repeated multiple, since
            #       it's a debug() message we don't care that much.
            msg = 'The URL "%s" has signs of HTML5 WebSockets usage, ' \
                  'but couldn\'t find any useful links.\n' \
                  'Perhaps links are dynamically created using javascript.\n' \
                  'Manual inspection of the page is recommended.'
            om.out.debug(msg % url)

        for ws_link in ws_links:
            desc = 'The URL: "%s" uses HTML5 websocket "%s"'
            desc = desc % (url, ws_link)

            i = Info('HTML5 WebSocket detected', desc, response.id,
                     self.get_name())
            i.set_url(url)
            i[WebSocketInfoSet.ITAG] = ws_link

            # Store found links
            self.kb_append_uniq_group(self, 'websockets_links', i,
                                      group_klass=WebSocketInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Finds ws:// or wss:// links within HTML or JavaScript documents.
        """


class WebSocketInfoSet(InfoSet):
    ITAG = 'ws_link'
    TEMPLATE = (
        'The application uses the HTML5 WebSocket URL {{ ws_link }} in'
        ' {{ uris|length }} different URLs. The first ten URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )