'''
web20Spider.py

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

from subprocess import call
import os.path
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.misc.decorators import runonce
from core.controllers.w3afException import w3afException, w3afRunOnce
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.parsers.urlParser import url_object
import core.controllers.outputManager as om
import core.data.constants.w3afPorts as w3afPorts
from core.controllers.daemons.proxy import proxy
from plugins.discovery.spiderMan import TERMINATE_URL, spiderMan

class web20Spider(spiderMan):

    def __init__(self):
        self._spider_js = os.path.join('plugins', 'discovery', 'web20Spider','spider.js')
        self._casperjs_bin = 'casperjs'
        super(web20Spider, self).__init__()

    @runonce(exc_class=w3afRunOnce)
    def discover(self, freq ):
        print 'web20Spider is running!'
        self._proxy = proxy(self._listenAddress, self._listenPort,
                            self._uri_opener, self.createPH())
        self._proxy.targetDomain = freq.getURL().getDomain()
        self._proxy.start2()

        call([
            self._casperjs_bin,
            '--proxy='+ self._listenAddress+':'+str(self._listenPort),
            self._spider_js,
            str(freq.getURL()),
            str(TERMINATE_URL)
            ])
        print 'web20Spider is finishing!'
        return self._fuzzableRequests

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''Purpose of this plugins is crawling of modern web app with help of integrated browser.
        '''
