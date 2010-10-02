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

import re

from plugins.grep.passwordProfilingPlugins.basePpPlugin import basePpPlugin

words_split_re = re.compile("[^\w]")

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
        
        data = {}

        if response.is_text_or_html():
            
            dom = response.getDOM()
            # Splitter function
            split = words_split_re.split
            # Filter function
            filter_by_len = lambda x: len(x) > 3

            # In some strange cases, we fail to normalize the document
            if dom is not None:
                
                for elem in dom.getiterator():
                    # Words inside <title> weights more.
                    inc = (elem.tag == 'title') and 5 or 1
                    text = elem.text
                    if text is not None:
                        # Filter by length of the word (> 3)
                        for w in filter(filter_by_len, split(text)):
                            if w in data:
                                data[w] += inc
                            else:
                                data[w] = inc
        return data
    
