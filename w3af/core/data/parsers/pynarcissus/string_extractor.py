"""
string_extractor.py

Copyright 2014 Andres Riancho

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
from .jsparser import parse


class StringExtractor(object):
    """
    This class was an experiment related with performance enhancements of w3af's
    parsers.

    There were many issues, one of them was that I was applying greedy
    regular expressions to all HTTP responses; so I thought it might be a good
    idea to actually parse JS and then extract links from the strings!

    Sadly parsing JS was really slow (at least for just extracting strings),
    both pynarcissus and pynoceros used 100% CPU for >=1.5 seconds to parse
    the latest jquery.

    If we compare that with just applying the regular expressions to the JS,
    which takes around 0.005 seconds... it simply makes no sense.

    Not removing this class because I believe it might be useful for the future,
    in case I actually want to do something advanced with a javascript source
    code.

    :see: https://github.com/andresriancho/w3af/issues/2104
    """
    CHILD_ATTRS = ['thenPart', 'elsePart', 'expression', 'body', 'initializer']
 
    def __init__(self, js_source):
        self.js_strings = set()

        try:
            root = parse(js_source)
        except Exception, e:
            pass
        else:
            self.visit(root)
 
    def visit(self, root):
        call = lambda n: getattr(self, "visit_%s" % n.type.lower(), self.noop)(n)

        call(root)

        self.visit_children(root)

        for node in root:
            self.visit(node)

    def visit_children(self, node):
        for attr in self.CHILD_ATTRS:
            child = getattr(node, attr, None)
            if child:
                self.visit(child)
 
    def noop(self, node):
        pass
 
    def visit_string(self, node):
        if node.type == "STRING":
            self.js_strings.add(node.value)

    def get_strings(self):
        return self.js_strings
