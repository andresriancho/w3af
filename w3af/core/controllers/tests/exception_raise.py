"""
exception_raise.py

Copyright 2012 Andres Riancho

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
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin


class exception_raise(CrawlPlugin):
    """
    This is a test plugin that will simply raise an exception
    
    Only useful for testing, see test_w3afcore.py

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # pylint: disable=E1102
    exception_to_raise = None
    
    def __init__(self):
        CrawlPlugin.__init__(self)

    def crawl(self, fuzzable_req):
        raise self.exception_to_raise('Test exception.')
