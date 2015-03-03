"""
kb_observer.py

Copyright 2015 Andres Riancho

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


class KBObserver(object):
    """
    When you want to listen to KB changes the best way is to create a KBObserver
    instance and call kb.add_observer(kb_observer). Then, the KB will call the
    methods in this instance to notify you about the changes.

    This is a base implementation that you should extend in order to provide
    real features. For now we just define the methods with a no-op
    implementation.

    Note that the methods in this class are named just like the ones in
    KnowledgeBase which trigger the calls.
    """
    def append(self, location_a, location_b, value, ignore_type=False):
        pass

    def add_url(self, url):
        pass

    def update(self, old_info, new_info):
        pass
