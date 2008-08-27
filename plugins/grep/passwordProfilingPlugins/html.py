'''
html.py

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

import core.controllers.outputManager as om
from plugins.grep.passwordProfilingPlugins.basePpPlugin import basePpPlugin
from core.data.getResponseType import *

import sgmllib

class html(basePpPlugin):
    '''
    This plugin creates a map of possible passwords by reading html responses.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        basePpPlugin.__init__(self)
        
    def getWords(self, response):
        '''
        Get words from the body, this is a modified "strings" that filters out HTML tags.
        
        @parameter body: In most common cases, an html. Could be almost anything.
        @return: A map of strings:repetitions.
        '''
        if response.is_text_or_html():
            sp = simpleParser()
            try:
                sp.parse( response.getBody() )
            except:
                # If this plugin couldnt parse the document, return None. This will indicate passwordProfiling.py to
                # continue to the next pp plugin.
                return None
            else:
                res = {}
                
                data = sp.getData()
                
                # I think that titles have more password material that normal data:
                titles = sp.getTitles()
                for t in titles.keys():
                    titles[ t ] *= 5
                
                # join both maps
                for i in titles.keys():
                    res[i] = titles[i]
                for i in data.keys():
                    res[i] = data[i]
                
                return res
    
class simpleParser(sgmllib.SGMLParser):
    "A simple parser class."

    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        sgmllib.SGMLParser.__init__(self, verbose)
        self._data = []
        self._titles = []
        self._inTitle = False

    def handle_data(self, data):
        "Handle the textual 'data'."
        if self._inTitle:
            self._titles.append( data )
        else:
            self._data.append(data)
        
    def start_title( self, data):
        "Handle titles."
        self._inTitle = True
        
    def end_title( self ):
        "Handle titles."
        self._inTitle = False

    def _parseStrings( self, stringList ):
        res = {}
        for d in stringList:
            d = d.replace('>', ' ')
            d = d.replace('<', ' ')
            splitted = d.split(' ')
            for chunk in splitted:
                if chunk.isalnum() and len(chunk) >= 4:
                    if chunk in res.keys():
                        res[ chunk ] += 1
                    else:
                        res[ chunk ] = 1
        return res
        
    def getData(self):
        "Return a map of string:repetitions"
        return self._parseStrings( self._data )
        
    def getTitles( self ):
        "Return a map of string:repetitions"
        return self._parseStrings( self._titles )
            
