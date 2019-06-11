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


class OrderedIterDefaultDict(defaultdict):
    def iteritems(self):
        for k in sorted(self.keys()):
            yield k, self[k]

    def __repr__(self):
        _repr = dict()
        for k, v in self.iteritems():
            _repr[k] = v
        return repr(_repr)


def url_tree_factory():
    return OrderedIterDefaultDict(url_tree_factory)


class URLNode(object):
    __slots__ = ('path', 'is_leaf')

    def __init__(self, path, is_leaf):
        self.path = path

        self.is_leaf = None
        self.set_is_leaf(is_leaf)

    def set_is_leaf(self, is_leaf):
        self.is_leaf = 1 if is_leaf else 0

    def __str__(self):
        return '<URLNode (path:"%s", is_leaf:%s)>' % (self.path, self.is_leaf)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        return self.path == other.path

    def __cmp__(self, other):
        return cmp(self.path, other.path)


class URLTree(object):
    def __init__(self):
        self.tree = url_tree_factory()

    def add_url(self, url):
        """
        Splits the URL by path and adds a new node to the tree for each
        """
        tree_nodes = self._url_to_tree_nodes(url)
        parent = None

        # Note: The last node from tree_nodes is always a leaf
        for node in tree_nodes:
            if parent is None:
                self._update_leaf_flag(self.tree, node)
                parent = self.tree[node]
            else:
                self._update_leaf_flag(parent, node)
                parent = parent[node]

    def _update_leaf_flag(self, parent, node):
        # If the node was already in the parent, it wasn't created
        # but it might need an update on it's leaf status
        if not node.is_leaf:
            return

        if node not in parent:
            return

        for n in parent:
            if node.path == n.path:
                n.set_is_leaf(True)

    def iteritems(self):
        for k, v in self.tree.iteritems():
            yield k, v

    def _url_to_tree_nodes(self, url):
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

        url_nodes = [URLNode(path, False) for path in tree_path if path]

        if url_nodes:
            leaf = url_nodes[-1]
            leaf.set_is_leaf(True)

        return url_nodes
