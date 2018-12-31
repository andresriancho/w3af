"""
hmap.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.plugins.infrastructure.oHmap.hmap as upstream_hmap

from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.info import Info


class hmap(InfrastructurePlugin):
    """
    Fingerprint the server type, i.e apache, iis, tomcat, etc.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # User configured parameters
        self._gen_fp = False
        self._threads = 4

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request):
        """
        It calls the "main" from hmap and writes the results to the kb.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        msg = 'Hmap web server fingerprint is starting, this may take a while.'
        om.out.information(msg)

        url = fuzzable_request.get_url()
        protocol = url.get_protocol()
        server = url.get_domain()
        port = url.get_port()
        ssl = False

        if protocol == 'https':
            ssl = True

        try:
            results = upstream_hmap.testServer(ssl, server, port, 1, self._gen_fp, self._threads)
        except BaseFrameworkException, w3:
            msg = 'A BaseFrameworkException occurred while running hmap: "%s"'
            om.out.error(msg % w3)
            return
        except Exception as e:
            msg = 'An unhandled exception occurred while running hmap: "%s"'
            om.out.error(msg % e)
            return

        #
        #   Found any results?
        #
        if not len(results):
            return

        server = results[0]

        desc = 'The most accurate fingerprint for this HTTP server is: "%s".'
        desc %= server

        i = Info('Webserver fingerprint', desc, 1, self.get_name())
        i['server'] = server
        om.out.information(i.get_desc())

        # Save the results in the KB so that other plugins can use this
        # information
        kb.kb.append(self, 'server', i)
        kb.kb.raw_write(self, 'server_string', server)

        #
        # Fingerprint file generated (this is independent from the results)
        #
        if self._gen_fp:
            msg = ('Hmap fingerprint file generated, please send a mail to'
                   ' w3af-develop@lists.sourceforge.net including the'
                   ' fingerprint file, your name and what server you'
                   ' fingerprinted. New fingerprints make the hmap plugin'
                   ' more powerful and accurate.')
            om.out.information(msg)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Generate a fingerprint file.'
        h = ('Define if we will generate a fingerprint file based on the'
             ' findings made during this execution.')
        o = opt_factory('gen_fingerprint', self._gen_fp, d, 'boolean', help=h)
        ol.add(o)

        d = 'Concurrent HTTP requests'
        h = ('Define how many threads are used to send HTTP requests to the'
             ' remote server. IoT devices might crash if this is set too high.')
        o = opt_factory('threads', self._threads, d, 'integer', help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._gen_fp = options_list['gen_fingerprint'].get_value()
        self._threads = options_list['threads'].get_value()

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        # I don't really use the server_header plugin here, but it is nice to have
        # two opinions about what we are dealing with.
        return ['infrastructure.server_header']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin fingerprints the remote web server and tries to determine
        the server type, version and patch level. It uses fingerprinting, not
        just the "Server" header returned by remote server. This plugin is a
        wrapper for Dustin Lee's hmap.

        Two configurable parameters exist:
            - gen_fingerprint
            - threads

        If gen_fingerprint is set to True, a fingerprint file is generated.
        Fingerprint files are used to identify web servers, if you generate new
        files please send them to the w3af-develop mailing list so we can add it
        to the framework.
        
        Hmap will use the user-configured number of threads to perform the
        fingerprinting process. This indicates how many requests are concurrently
        sent to the server by hmap.        

        One important thing to notice is that hmap connects directly to the
        remote web server, without using the framework's HTTP configurations
        (like proxy or authentication).
        """
