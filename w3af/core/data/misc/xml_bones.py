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
from w3af.core.data.constants.encodings import DEFAULT_ENCODING


ROUND = 20.0


def round_N(num):
    return int(round(num / ROUND) * ROUND)


def get_xml_bones(document):
    """
    This function returns the "bones" of an XML document, replacing all the
    text-data and attribute values with a round(length)

    For example:

        <xml></xml>                  --->    xml0/xml
        <xml>hello</xml>             --->    xml0/xml
        <xml attr=123>hello</xml>    --->    xmlattr00/xml

    See test_xml_bones for more examples.

    :param document: An XML document as a string
    :return: The bones of the XML document, which is commonly used as an input
             for a hash function, which is then used as a key for an LRU.
    """
    parser = etree.HTMLParser(target=BoneCollector(),
                              no_network=True,
                              recover=True,
                              encoding=DEFAULT_ENCODING,
                              remove_comments=True,
                              remove_pis=True)

    document = smart_str_ignore(document, encoding=DEFAULT_ENCODING)
    etree.parse(StringIO(document), parser)

    # pylint: disable=E1101
    return ''.join(parser.target.bones)


class BoneCollector(object):

    __slots__ = ('bones',)

    def __init__(self):
        self.bones = []

    def start(self, tag, attrib):
        self.bones.append(tag)

        for attr, value in attrib.iteritems():
            args = (attr, round_N(len(value)))
            self.bones.append('%s%s' % args)

    def end(self, tag):
        self.bones.append(tag)

    def data(self, data):
        self.bones.append('%s' % round_N(len(data)))

    def comment(self, text):
        pass

    def close(self):
        return None


def get_xml_bones_iterparse(document, _round_N=round_N):
    """
    This is the iterparse version of get_xml_bones()

    Reading some documents on lxml performance it felt like a good idea to
    implement it using iterparse... measured... and this is actually slower

    Leaving here as a reference and reminder that get_xml_bones() can not
    be improved this way.

    :param document: An XML document as a string
    :return: The bones of the XML document, which is commonly used as an input
             for a hash function, which is then used as a key for an LRU.
    """
    if not document:
        return ''

    output = []
    append = output.append

    document = smart_str_ignore(document, encoding=DEFAULT_ENCODING)
    document_io = StringIO(document)
    events = {'start', 'end'}

    context = etree.iterparse(document_io,
                              events=events,
                              remove_comments=True,
                              remove_pis=True,
                              html=True,
                              recover=True,
                              encoding=DEFAULT_ENCODING,
                              huge_tree=False,
                              resolve_entities=False)

    for event, elem in context:
        if event == 'start':
            append(elem.tag)

            for attr, value in elem.attrib.iteritems():
                append('%s%s' % (attr, _round_N(len(value))))

            if elem.text is not None:
                append('%s' % _round_N(len(elem.text)))

        else:
            append('/%s' % elem.tag)

    return ''.join(output)
