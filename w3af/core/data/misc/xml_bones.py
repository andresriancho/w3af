"""
xml_bones.py

Copyright 2019 Andres Riancho

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
from lxml import etree
from cStringIO import StringIO

from w3af.core.data.misc.encoding import smart_str_ignore


ROUND = 20.0


def round_N(num):
    return int(round(num / ROUND) * ROUND)


def get_xml_bones(document):
    """
    This function returns the "bones" of an XML document, extracting all the
    text-data and attribute values.

    For example:

        <xml></xml>                  --->    xml/xml
        <xml>hello</xml>             --->    xml/xml
        <xml attr=123>hello</xml>    --->    xmlattr/xml

    :param document: An XML document as a string
    :return: The bones of the XML document, which is commonly used as an input
             for a hash function, which is then used as a key for an LRU.
    """
    parser = etree.HTMLParser(target=BoneCollector(),
                              no_network=True,
                              recover=True)

    document = smart_str_ignore(document)
    etree.parse(StringIO(document), parser)

    return ''.join(parser.target.bones)


class BoneCollector(object):
    def __init__(self):
        self.bones = []

    def start(self, tag, attrib):
        self.bones.append(tag)

        for attr, value in attrib.iteritems():
            args = (attr, round_N(len(value)))
            self.bones.append('%s%s' % args)

    def end(self, tag):
        self.bones.append('/%s' % tag)

    def data(self, data):
        self.bones.append('%s' % round_N(len(data)))

    def comment(self, text):
        pass

    def close(self):
        return ''
