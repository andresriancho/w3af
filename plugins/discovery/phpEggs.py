'''
phpEggs.py

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
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afRunOnce
import core.data.kb.info as info
from core.controllers.misc.levenshtein import relative_distance
import core.data.parsers.urlParser as urlParser
import md5

class phpEggs(baseDiscoveryPlugin):
    '''
    Fingerprint the PHP version using documented easter eggs that exist in PHP.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._exec = True
        
        # Already analyzed extensions
        self._already_analyzed_ext = []
        
        # This is a list of hashes and description of the egg for every PHP version.
        self._eggDB = {}
        self._eggDB['4.1.2'] = [('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\x85\xbe;K\xe7\xbf\xe89\xcb\xb3\xb4\xf2\xd3\x0f\xf9\x83', 'PHP Logo 2'),     ('tJ\xec\xef\x04\xf9\xed\x1b\xc3\x9a\xe7s\xc4\x00\x17\xd1', 'PHP Credits'),     ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.2.2'] = [('\x85\xbe;K\xe7\xbf\xe89\xcb\xb3\xb4\xf2\xd3\x0f\xf9\x83', 'PHP Logo 2'), ('u\x8c\xca\xa9\tL\xde\xed\xcf\xc6\x00\x17\xe7h\x13~', 'PHP Credits'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f','PHP Logo'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]

        self._eggDB['4.3.2'] =[('\x8a\x8bJA\x91\x03\x07\x8d\x82p|\xf6\x82&\xa4\x82', 'PHP Credits'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ("\xa5{\xd7>'\xbe\x03\xa6-\xd6\xb3\xe1\xb57\xa7,", 'PHP Logo 2'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.3.8'] = [('\x96qJ\x0f\xbe#\xb5\xc0|\x8b\xe3C\xad\xb1\xba\x90', 'PHP Credits'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ("\xa5{\xd7>'\xbe\x03\xa6-\xd6\xb3\xe1\xb57\xa7,", 'PHP Logo 2'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.3.9'] = [('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'),    ('\xf9\xb5k6\x1f\xaf\xd2\x8bf\x8c\xc3I\x84%\xa2;', 'PHP Credits'),  ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]  
        self._eggDB['4.3.10'] = [('\x8f\xbfH\xd5\xa2\xa6@e\xfc&\xdb>\x89\x0b\x98q', 'PHP Credits'),('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]  
        self._eggDB['4.3.10'] =[('\x8f\xbfH\xd5\xa2\xa6@e\xfc&\xdb>\x89\x0b\x98q', 'PHP Credits'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo'), ("\xa5{\xd7>'\xbe\x03\xa6-\xd6\xb3\xe1\xb57\xa7,", 'PHP Logo 2')]
        self._eggDB['4.3.10'] = [('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\x1e\x8f\xe4\xae\x1b\xf0k\xe2"\xc1d=2\x01_\x0c', 'PHP Credits'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo'), ("\xa5{\xd7>'\xbe\x03\xa6-\xd6\xb3\xe1\xb57\xa7,", 'PHP Logo 2')]
        self._eggDB['4.3.10-18'] = [('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'), ('\x1e\x8f\xe4\xae\x1b\xf0k\xe2"\xc1d=2\x01_\x0c', 'PHP Credits'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]

        self._eggDB['4.3.11'] =[('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'),   ('\x8f\xbfH\xd5\xa2\xa6@e\xfc&\xdb>\x89\x0b\x98q', 'PHP Credits'),  ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'),    ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.3.11'] = [('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'),('<\xab\x8f\xef\n\xe2\xa4\xe9\x1eE\x1c;AWz<', 'PHP Credits'),('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.3.11'] = [('C\xc6v\xb5\xe3\xd6<]\xf0\x1by\xb2\xdc\xb0\\\x08', 'PHP Logo 2'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\x1e\x8f\xe4\xae\x1b\xf0k\xe2"\xc1d=2\x01_\x0c', 'PHP Credits'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.3.11'] = [('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\xa8\xad2>\x83\x7f\xa0\x07q\xed\xa6\xb7\t\xf4\x0e7', 'Zend Logo'), ('\x1e\x8f\xe4\xae\x1b\xf0k\xe2"\xc1d=2\x01_\x0c', 'PHP Credits'), ('\xa8\xad2>\x83\x7f\xa0\x07q\xed\xa6\xb7\t\xf4\x0e7', 'PHP Logo 2')]

        self._eggDB['4.4.0'] = [('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'),   ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'),    ('\xdd\xf1n\xc6~\x07\x0e\xc6$~\xc1\x90\x8cR7~', 'PHP Credits'),     ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.4.0 for Windows'] =[('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo'), ('m\x97Csh>\xcf\xcf0\xa7\xf6\x87?-#J', 'PHP Credits')]

        self._eggDB['4.4.4'] = [('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'),   ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'),    ('\xbe\xd7\xce\xff\t\xe9fm\x96\xfd\xf3Q\x8a\xf7\x8e\x0e', 'PHP Credits'),   ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.4.7'] = [('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'),   ('i*\x87\xca,QR<\x17\xf5\x97%6S\xc7w', 'PHP Credits'),  ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'),    ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]

        self._eggDB['4.4.7'] = [('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('r\xb7\xad`O\xe16/\x1e\x8b\xf4\xf6\xd8\rN\xdc', 'PHP Credits'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo')]
        self._eggDB['4.4.8'] = [('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo'), ('L\xdf\xec\x8c\xa1\x16\x91\xa4oOc\x83\x9eU\x9f\xc5', 'PHP Credits')]

        self._eggDB['4.4.4-8+etch6'] = [('1\xa2U>\xfc4\x8a!\xb8^`n^l$$', 'PHP Credits'), ('\x11\xb9\xcf\xe3\x06\x00O\xceY\x9a\x1f\x81\x80\xb6\x12f', 'PHP Logo'), ('\xda-\xae\x87\xb1f\xb7p\x9d\xbd@a7[t\xcb', 'Zend Logo'),
('K,\x92@\x9c\xf0\xbc\xf4e\xd1\x99\xe9:\x15\xac?', 'PHP Logo 2')]

        self._eggDB['5.0.3'] = [('7\xe1\x94\xb7\x99\xd4\xaa\xff\x10\xe3\x9cN;&y\xa2', 'PHP Logo 2'), ('\xde\xf6\x1a\x12\xc3\xb0\xa53\x14h\x10@=2TQ', 'PHP Credits'), ('\x8a\xc5\xa6\x86\x13[\x926d\xf6O\xe7\x18\xeaU\xcd', 'PHP Logo'),
('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]
        self._eggDB['5.1.1'] =[('U\x18\xa0*\xf4\x14x\xcf\xc4\x92\xc90\xac\xe4Z\xe5', 'PHP Credits'), ('\x8a\xc5\xa6\x86\x13[\x926d\xf6O\xe7\x18\xeaU\xcd', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]

        self._eggDB['5.1.6'] = [('\x82\xfa-j\xa1_\x97\x1f}\xad\xef\xe4\xf2\xac \xe3', 'PHP Credits'),   ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'),  ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]   
        self._eggDB['5.1.6'] = [('\x82\xfa-j\xa1_\x97\x1f}\xad\xef\xe4\xf2\xac \xe3', 'PHP Credits'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2')]
        self._eggDB['5.1.6'] = [('Kh\x93\x16@\x9e\xb0\x9b\x15XR\xe0\x06W\xa0\xae', 'PHP Credits'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]

        self._eggDB['5.2.0'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('\xe5fq[\xcb\x0f\xd2\xcb\x1d\xc4>\xd0v\xc0\x91\xf1', 'PHP Credits')]
        self._eggDB['5.2.0-8+etch7'] =[('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ("j\x1c!\x1f'3\x0f\x1a\xb6\x02\xc7\xc5t\xf3\xa2y", 'PHP Credits'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]
        self._eggDB['5.2.0-8+etch10'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('0\x7fZ\x1c\x02\x15\\\xa3\x87Dd~\xb9K5C', 'PHP Credits')]
        self._eggDB['5.2.0-8+etch10'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('\xe5fq[\xcb\x0f\xd2\xcb\x1d\xc4>\xd0v\xc0\x91\xf1', 'PHP Credits')]
        self._eggDB['5.2.0-8+etch7'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('0\x7fZ\x1c\x02\x15\\\xa3\x87Dd~\xb9K5C', 'PHP Credits')]

        self._eggDB['5.2.1'] = [('\xd3\x89N\x19#=\x97\x9d\xb0}b?`\x8bn\xce', 'PHP Credits'),('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'),    ('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2')]
        self._eggDB['5.2.2'] = [('\x84\x17\xe0\xaf&\xb6\xf1F\xea\xf19(\x80\xf5\x8a[', 'PHP Credits'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2')]

        self._eggDB['5.2.2'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ('V\xf985\x87\xeb\xcc\x94U\x8e\x11\xec\x08XO\x05', 'PHP Credits'),  ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'),  ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]
        self._eggDB['5.2.3-1+b1'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'),    ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'),  ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'),   ('\xc3|\x96\xe8r\x8d\xc9Y\xc5R\x19\xd4\x7f-T?', 'PHP Credits')]     
        self._eggDB['5.2.3'] = [('Ny\xe2\xca\xde\x96\xe4\x191\xf3\xf6\x81\xccI\xb6\n', 'PHP Credits'), ('Ny\xe2\xca\xde\x96\xe4\x191\xf3\xf6\x81\xccI\xb6\n', 'PHP Logo'), ('Ny\xe2\xca\xde\x96\xe4\x191\xf3\xf6\x81\xccI\xb6\n', 'PHP Logo 2'), ('Ny\xe2\xca\xde\x96\xe4\x191\xf3\xf6\x81\xccI\xb6\n', 'Zend Logo')]

        self._eggDB['5.2.4'] = [('\x8f\xe9z\x7f\xa0,)Q\x1dR\x07\xa8G\xa6\x91\xff','PHP Logo'), ('\x8f\xe9z\x7f\xa0,)Q\x1dR\x07\xa8G\xa6\x91\xff', 'ZendLogo'), ('\x8f\xe9z\x7f\xa0,)Q\x1dR\x07\xa8G\xa6\x91\xff', 'PHP Credits'),('\x8f\xe9z\x7f\xa0,)Q\x1dR\x07\xa8G\xa6\x91\xff', 'PHP Logo 2')]
        self._eggDB['5.2.4'] = [('t\xc3:\xb9t]\x02+\xa6\x1b\xc4:]\xb7\x17\xeb', 'PHP Credits'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2')]

        self._eggDB['5.2.5-3'] = [('\x01R\xedi_B\x91H\x87A\xd9\x8b\xa0f\xd2\x80', 'PHP Logo 2'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('\xb7\xe48[\xd7\xf0~7\x8d\x92H[G"\xc1i', 'PHP Credits'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]
        self._eggDB['5.2.5'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'),    ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'),  ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'),   ('\xc3|\x96\xe8r\x8d\xc9Y\xc5R\x19\xd4\x7f-T?', 'PHP Credits')]     
        self._eggDB['5.2.5'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('\xf2b\x85(\x11 \xa2)`r\xf2\x1e!\xe7\xb4\xb0', 'PHP Credits'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo')]
        self._eggDB['5.2.6'] =[('\xbb\xd4L \xd5a\xa0\xfcZJ\xa7`\x93\xd5@\x0f', 'PHP Credits'),('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'),('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2')]
        self._eggDB['5.2.6RC4-pl0-gentoo'] = [('P\xca\xaf&\x8bO=&\rr\n\x1a)\xc5\xfe!', 'PHP Logo 2'), ('\xc4\x8b\x07\x89\x99\x17\xdf\xb5\xd5\x91\x03 \x07\x04\x1a\xe3', 'PHP Logo'), ('vu\xf1\xd0\x1c\x92\x7f\x9ejGR\xcf\x18#E\xa2', 'Zend Logo'), ('\xd0;$\x81\xf6\r\x9ed\xcb\\\x0fK\xd0\xc8~\xc1', 'PHP Credits')]

        
    def discover(self, fuzzableRequest ):
        '''
        Nothing strange, just do some GET requests to the eggs and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # Get the extension of the URL (.html, .php, .. etc)
            ext = urlParser.getExtension( fuzzableRequest.getURL() )
            
            # Only perform this analysis if we haven't already analyzed this type of extension
            # OR if we get an URL like http://f00b5r/4/     (Note that it has no extension)
            # This logic will perform some extra tests... but we won't miss some special cases
            # Also, we aren't doing something like "if 'php' in ext:" because we never depend
            # on something so changable as extensions to make decisions.
            if ext == '' or ext not in self._already_analyzed_ext:
                
                # Init some internal variables
                getResults = []
                originalResponse = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
                
                # Perform the GET requests to see if we have a phpegg
                for egg, desc in self._getEggs():
                    eggURL = urlParser.uri2url( fuzzableRequest.getURL() ) + egg
                    try:
                        response = self._urlOpener.GET( eggURL, useCache=True )
                    except KeyboardInterrupt,e:
                        raise e
                    else:
                        if relative_distance( originalResponse.getBody(), response.getBody() ) < 0.1:
                            # Found an egg, save it.
                            i = info.info()
                            i.setName('PHP Egg - ' + desc)
                            i.setURL( eggURL )
                            i.setDesc( 'The PHP framework running on the remote server has a "'+ desc +'" easter egg, example URL: '+  eggURL )
                            kb.kb.append( self, 'eggs', i )
                            om.out.information( i.getDesc() )
                            
                            getResults.append( (response, desc) )
                            self._exec = False
                
                # analyze the info to see if we can identify the version
                self._analyzeEgg( getResults )
                
                # Now we save the extension as one of the already analyzed
                if ext != '':
                    self._already_analyzed_ext.append(ext)
        
        return []
    
    def _analyzeEgg( self, response ):
        '''
        Analyzes the eggs and tries to deduce a PHP version number ( which is saved to the kb ).
        '''
        if not response:
            return None
        else:
            cmpList = []
            for r in response:
                cmpList.append( (md5.new(r[0].getBody()).digest(), r[1] ) )
            cmpSet = set( cmpList )
            
            found = False
            matchingVersions = []
            for version in self._eggDB:
                versionHashes = set( self._eggDB[ version ] )
            
                if len( cmpSet ) == len( cmpSet.intersection( versionHashes ) ):
                    matchingVersions.append( version )
                    found = True
            
            if matchingVersions:
                i = info.info()
                i.setName('PHP Egg')
                i.setDesc( 'The PHP framework version running on the remote server was identified as: '+  ' / '.join(matchingVersions) )
                i['version'] = matchingVersions
                kb.kb.append( self, 'version', i )
                om.out.information( i.getDesc() )

            if not found:
                version = 'unknown'
                poweredByHeaders = kb.kb.getData( 'serverHeader' , 'poweredByString' )
                try:
                    for v in poweredByHeaders:
                        if 'php' in v.lower():
                            version = v.split('/')[1]
                except:
                    pass
                om.out.information('The PHP version could not be identified using PHP eggs, please send this signature and the \
PHP version to the w3af project. Signature: self._eggDB[\''+ version + '\'] = ' + str(list(cmpSet)) )
                om.out.information('The serverHeader plugin reported this PHP version: ' + version )
            
    def _getEggs( self ):
        '''
        @return: A list of tuples with the egg url and a description.
        '''
        res = []
        res.append( ('?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000', 'PHP Credits') )
        res.append( ('?=PHPE9568F34-D428-11d2-A769-00AA001ACF42', 'PHP Logo') )
        res.append( ('?=PHPE9568F35-D428-11d2-A769-00AA001ACF42', 'Zend Logo') )
        res.append( ('?=PHPE9568F36-D428-11d2-A769-00AA001ACF42', 'PHP Logo 2') )
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.serverHeader']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find the documented easter eggs that exist in PHP and identify
        the remote PHP version using the easter egg content. The easter eggs that this plugin
        verifies are:
        
            - http://php.net/?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000 ( PHP Credits )
            - http://php.net/?=PHPE9568F34-D428-11d2-A769-00AA001ACF42  ( PHP Logo )
            - http://php.net/?=PHPE9568F35-D428-11d2-A769-00AA001ACF42  ( Zend Logo )
            - http://php.net/?=PHPE9568F36-D428-11d2-A769-00AA001ACF42  ( PHP Logo 2 )
        '''
