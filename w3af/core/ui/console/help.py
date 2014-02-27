"""
help.py

Copyright 2008 Andres Riancho

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
import os.path

from string import Template
from xml.dom.minidom import *

try:
    import xml.etree.ElementTree as ET
except ImportError:
    try:
        # we're using Python 2.4
        import elementtree.ElementTree as ET
    except ImportError:
        import sys
        print 'It seems that your python installation doesn\'t have element tree',
        print 'installed. Please install it and run w3af again.'
        sys.exit(-9)

from w3af import ROOT_PATH


class helpRepository(object):
    """
    This class wraps a help file and allows to extract context-related help objects

    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    """
    
    DEFAULT_PATH = os.path.join(ROOT_PATH, 'core', 'ui', 'console', 'help.xml')
    
    def __init__(self, path=DEFAULT_PATH):
        self.__doc = ET.parse(path)
        self.__map = {}
        topics = self.__doc.findall('.//topic')
        for t in topics:
            self.__map[str(t.attrib['name'])] = t

    def load_help(self, topic, obj=None, vars=None):
        """
        Loads an object from the repository.
        :param topic: the name of a context (for example, menu)
        :param obj: the help object where to load the help data
        (if None, a new one is created)
        :param vars: a dict of variables to replace in the help text
        """

        #a closure to simplify the substitution
        def subst(templ):
            if not vars:
                return templ
            return Template(templ).safe_substitute(vars)

        if not obj:
            obj = HelpContainer()
        elt = self.__map[topic]
        for catElt in elt.findall('category'):
            catName = 'name' in catElt.attrib and catElt.attrib[
                'name'] or 'default'
            catName = str(catName)

            for itemElt in catElt.findall('item'):
                itemName = str(itemElt.attrib['name'])
                itemName = subst(itemName)

                short = itemElt.findtext('head')
                full = itemElt.findtext('body')

                if not short:
                    short = itemElt.text

                short = subst(short)
                if full:
                    full = subst(full)

                #    The help.xml file is in unix format, meaning that it only
                #    has \n for new lines. This will bring some issues when
                #    printing the data to the console since the \r is required
                #    there, so I simply add the \r here.
                short = short.replace('\n', '\r\n')
                if full:
                    full = full.replace('\n', '\r\n')

                obj.add_help_entry(itemName, (short, full), catName)

        return obj

# main repository
helpMainRepository = helpRepository()


class HelpContainer(object):
    """
    Container for help items.
    """
    def __init__(self):
        self._table = {}
        self._subj2Gat = {}
        self._cat2Subj = {}

    def add_help_entry(self, subj, content, cat=''):
        """
        Adds the help entry.
        :param content: usually a tuple like (head, body)
        :param cat: a name of the category.
        If the item exists in an other category, it will be replaced.
        """

        if type(content) not in (tuple, list):
            content = (content, None)

        self._table[subj] = content
        self._subj2Gat[subj] = cat
        if cat in self._cat2Subj:
            d = self._cat2Subj[cat]
        else:
            d = []
            self._cat2Subj[cat] = d

        d.append(subj)

    def get_categories(self):
        return self._subj2Gat.keys()

    def add_help(self, table, cat=''):
        for subj in table:
            self.add_help_entry(subj, table[subj], cat)

    def get_help(self, subj):
        if subj not in self._table:
            return (None, None)

        return self._table[subj]

    def get_items(self):
        return self._table.keys()

    def get_plain_help_table(self, separators=True, cat=None):
        """
        Returns a table of format 'subject -> head'
        to display with the table.py module
        :param separators: if True, the categories are separated
        by extra line.
        :param cat: category to include into the page.
        If None, all are included.
        """
        result = []

        if cat is not None:
            self._appendHelpTable(result, cat)
        else:
            for g in self._cat2Subj:
                self._appendHelpTable(result, g)
                if separators:
                    result.append([])

            if len(result) and separators:
                result.pop()

        return result

    def _appendHelpTable(self, result, cat):
        items = cat in self._cat2Subj and self._cat2Subj[cat] or self._table

        for subj in items:
            result.append([subj, self.get_help(subj)[0]])
