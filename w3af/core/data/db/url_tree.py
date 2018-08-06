"""
url_tree.py

Copyright 2018 Andres Riancho

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

from collections import defaultdict


def url_tree_factory():
    return defaultdict(url_tree_factory)


class URLTree(object):
    def __init__(self):
        self.tree = url_tree_factory()

    def add_url(self, url):
        """
        Splits the URL by path and adds a new node to the tree for each
        """
        tree_path = self._url_to_tree_path(url)
        parent = None

        for path in tree_path:
            if parent is None:
                parent = self.tree[path]
            else:
                parent = parent[path]

    def iteritems(self):
        for k, v in self.tree.iteritems():
            yield k, v

    def _url_to_tree_path(self, url):
        """
        Split the path into pieces, each piece if a key in the tree. For example:

            http://foo.com/bar/123.txt
            ['http://foo.com', '/bar/', '123.txt']

        :param url: A URL instance
        :return: The split URL
        """
        tree_path = []

        protocol_domain = u'%s://%s' % (url.get_protocol(), url.get_net_location())
        tree_path.append(protocol_domain)

        path = url.get_path()
        split_path = path.split(u'/')

        tree_path.extend(split_path)

        return [i for i in tree_path if i]
