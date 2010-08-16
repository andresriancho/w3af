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

from plugins.grep.passwordProfilingPlugins.basePpPlugin import basePpPlugin


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

            # In some strange cases, we fail to normalize the document
            if dom != None:

                title_elements = dom.findall('title')
                title_words = []
                for element in title_elements:
                    title_words.extend( element.text.split(' ') )
                title_words = [ w.strip() for w in title_words if len(w) > 3 ]
                
                all_strings_list = [tag.text for tag in dom.iter()]
                all_words = []
                for a_string in all_strings_list:
                    if a_string != None:
                        all_words.extend( a_string.split(' ') )
                all_words = [ w.strip() for w in all_words if len(w) > 3 ]

                for word in title_words:
                    if word in data:
                        data[ word ] += 5
                    else:
                        data[ word ] = 5
                
                for word in all_words:
                    if word in data:
                        data[ word ] += 1
                    else:
                        data[ word ] = 1
            
            return data
    
