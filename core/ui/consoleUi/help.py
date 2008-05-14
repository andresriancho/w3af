'''
help.py

Copyright 2008 Andres Riancho

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

from string import Template
from xml.dom.minidom import *
import os.path

try:
    import xml.etree.ElementTree as ET
except ImportError:
    # we're using Python 2.4
    import elementtree.ElementTree as ET
    

class helpRepository:
    '''
    This class wraps a help file and allows to extract 
    context-related help objects
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''
    def __init__(self, path=os.path.join('core','ui','consoleUi','help.xml') ):
        self.__doc = ET.parse(path)
        self.__map = {}
        topics = self.__doc.findall('.//topic')
        for t in topics:
            self.__map[str(t.attrib['name'])] = t


    def loadHelp(self, topic, obj=None, vars=None):
        '''
        Loads an object from the repository.
        @parameter topic: the name of a context (for example, menu)
        @parameter obj: the help object where to load the help data 
        (if None, a new one is created)
        @parameter vars: a dict of variables to replace in the help text
        '''

        #a closure to simplify the substitution
        def subst(templ):
            if not vars:
                return templ
            return Template(templ).safe_substitute(vars)

        if not obj:
            obj = help()
        elt = self.__map[topic]
        for catElt in elt.findall('category'):
            catName = 'name' in catElt.attrib and catElt.attrib['name'] or 'default'
            catName = str(catName)

            for itemElt in catElt.findall('item'):
                itemName = str( itemElt.attrib['name'] )
                itemName = subst(itemName)

                short = itemElt.findtext('head')
                full = itemElt.findtext('body')
                
                if not short:
                    short = itemElt.text

                short = subst(short)
                if full:
                    full = subst(full)

                obj.addHelpEntry(itemName, (short, full), catName)


        return obj

# main repository
helpMainRepository = helpRepository()

    
class help:
    '''
    Container for help items.
    '''
    def __init__(self):
        self._table = {}
        self._subj2Gat = {}
        self._cat2Subj = {}


    def addHelpEntry(self, subj, content, cat=''):
        '''
        Adds the help entry.
        @parameter content: usually a tuple like (head, body)
        @parameter cat: a name of the category. 
        If the item exists in an other category, it will be replaced.
        '''

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


    def getCategories(self):
        return self._subj2Gat.keys()

    def addHelp(self, table, cat=''):
        for subj in table:
            self.addHelpEntry(subj, table[subj], cat)


    def getHelp(self, subj):
        if subj not in self._table:
            return (None, None)

        return self._table[subj]


    def getItems(self):
        return self._table.keys()


    def getPlainHelpTable(self, separators=True, cat=None):
        '''
        Returns a table of format 'subject -> head' 
        to display with the table.py module
        @parameter separators: if True, the categories are separated 
        by extra line.
        @parameter cat: category to include into the page. 
        If None, all are included.
        '''
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
            result.append([subj, self.getHelp(subj)[0]])
        
