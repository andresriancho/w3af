'''
ds_store.py

Copyright 2013 Tomas Velazquez

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
from struct import unpack

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.constants.severity as severity

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afException
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.data.db.disk_set import DiskSet
from core.data.kb.vuln import Vuln


class ds_store(CrawlPlugin):
    '''
    Search .DS_Store file and checks for files containing.
    :author: Tomas Velazquez ( tomas.velazquezz@gmail.com )
    :credits: This code was based in cpan Mac::Finder::DSStore by Wim Lewis ( wiml@hhhh.org )
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = DiskSet()
        self._ds_store = '.DS_Store'
        self._store = None
        self._offset = 0
        self._filenames = DiskSet()
        self._data = ''
        self._is_vuln = False

    def _open(self, data):
        '''
        Open a .DS_Store file
        :param data: file content
        '''
        self._data = data
        (magic1, magic, offset, size, offset2) = unpack('>5I', self._data[:20])
        magic = self._data[4:8]

        if magic != 'Bud1' or magic1 != 1:
            return False

        if offset != offset2:
            return False

        rootblock = self._data[offset:offset+size]
        offsetcount, = unpack('>I', rootblock[4:8])
        offsets = []
        _offset = 12

        while offsetcount > 0:
            offsets.extend(unpack('>256I', rootblock[_offset:_offset+1024]))
            offsetcount -= 256
            _offset += 1024

        offsets = filter(lambda x: x!=0, offsets)
        toccount, = unpack('>I', rootblock[_offset:_offset+4])
        _offset += 4
        toc = {}

        while toccount > 0:
            _len, = unpack('b', rootblock[_offset:_offset+1])
            _offset += 1
            _name = rootblock[_offset:_offset+_len]
            _offset += _len
            _value, = unpack('>I', rootblock[_offset:_offset+4])
            _offset += 4
            toc[_name] = _value
            toccount -= 1

        store = {}
        store['offsets'] = offsets
        store['toc'] = toc

        return store

    def _read_filename(self, block):
        '''
        Read the filename from a block
        :param block: data struct to analyze
        '''
        flen, = unpack('>I', block[self._offset:self._offset+4])
        self._offset += 4
        filename = block[self._offset:self._offset+2*flen]
        self._offset += 2*flen
        filename = filename.decode('utf-16be')
        self._filenames.add(filename)

        return filename

    def _read_entry(self, block):
        '''
        Read the entry from a block
        :param block: data struct to analyze
        '''
        filename = self._read_filename(block)
        self._offset += 4
        struct_type = block[self._offset:self._offset+4]
        self._offset += 4

        if struct_type in ['bool', 'long', 'shor', 'type']:
            self._offset += 4
        elif struct_type == 'blob':
            bloblen, = unpack('>I', block[self._offset:self._offset+4])
            self._offset += 4 + bloblen
        elif struct_type == 'ustr':
            strlen, = unpack('>I', block[self._offset:self._offset+4])
            self._offset += 4 + 2 * strlen
        else:
            msg = ('Error: unknown type "%s" submit it to w3af team')
            om.out.information( msg % (struct_type))

        return filename

    def _read_btree_node(self, node):
        '''
        Read a btree node from a node
        :param node: data struct to analyze
        '''
        self._offset = 0
        pointer, = unpack('>I', node[self._offset:self._offset+4])
        self._offset += 4
        count, = unpack('>I', node[self._offset:self._offset+4])
        self._offset += 4

        if pointer > 0:
            pointers = []
            values = []

            while count > 0:
                p, = unpack('>I', node[self._offset:self._offset+4])
                self._offset += 4
                pointers.append(p)
                v = self._read_entry(node)
                values.append(v)
                count -= 1

            pointers.append(pointer)

            return (values, pointers)
        else:
            values = []

            while count > 0:
                v = self._read_entry(node)
                values.append(v)
                count -= 1

        return (values, [])

    def _traverse_btree(self, node):
        '''
        Traverse btree node
        :param node: node to analyze
        '''
        (values, pointers) = self._read_btree_node(self._block_by_number(node))
        count = len(values)

        if pointers != []:
            count += self._traverse_btree(pointers.pop())
            while len(values) > 0 and pointers != []:
                count += self._traverse_btree( pointers.pop() )

        return count

    def _get_dsdb_entries(self):
        '''
        Get DSDB entries
        '''
        (rootnode, _, nrec) = self._get_btree_rootblock()
        num = self._traverse_btree(rootnode)

        if num != nrec:
            msg = ('Header node count (%d) not equal to actual node count (%d)')
            om.out.debug( msg % (nrec, num) )

        return self._filenames

    def _new(self, offset, size):
        '''
        Get a specified node
        :param offset: data offset
        :param size: data length
        '''
        offset += 4
        value = self._data[offset:offset+size]

        return value

    def _block_by_number(self, _id):
        '''
        Get a block from a number
        :param _id: identificator number
        '''
        addr = self._store['offsets'][_id]

        if not addr:
            return None

        offset = addr & ~0x1F   
        _len = 1 << ( addr & 0x1F )
        om.out.debug('  node id %d is %d bytes at 0x%x' % (_id, _len, offset))
        block = self._new(offset, _len)

        return block

    def _get_btree_rootblock(self):
        '''
        Get btree root block
        '''
        _id = self._store['toc']['DSDB']
        return unpack('>3I', self._block_by_number(_id)[0:12])

    def crawl(self, fuzzable_request):
        '''
        For every directory, fetch a list of files and analyze the response.
        
        :parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        for domain_path in fuzzable_request.get_url().get_directories():
            if domain_path not in self._analyzed_dirs:
                self._analyzed_dirs.add( domain_path )
                self._check_and_analyze( domain_path )

    def _check_and_analyze(self, domain_path):
        '''
        Check if a .DS_Store filename exists in the domain_path.
        :return: None, everything is saved to the self.out_queue.
        '''
        # Request the file
        url = domain_path.url_join( self._ds_store )
        try:
            response = self._uri_opener.GET( url, cache=True )
        except w3afException,  w3:
            msg = ('Failed to GET .DS_Store file: %s. Exception: %s.')
            om.out.debug( msg, (url, w3) )
        else:
            # Check if it's a .DS_Store file
            if not is_404( response ):
                self._is_vuln = False
                parsed_url_list = []
                self._store = self._open( response.get_body() )
                if self._store:
                    ents = self._get_dsdb_entries()

                    for filename in ents:
                        parsed_url_list.append(domain_path.url_join(filename))

                #self._tm.threadpool.map(self._get_and_parse, parsed_url_list)
                self.worker_pool.map(self._get_and_parse, parsed_url_list)
                
                if self._is_vuln:
                    desc = 'A .DS_Store file was found at: %s. The contents'\
                           ' of this file disclose filenames'
                    desc = desc % (response.get_url())

                    v = Vuln('.DS_Store file found', desc, severity.LOW,
                             response.id, self.get_name())
                    v.set_url(response.get_url())

                    kb.kb.append( self, 'ds_store', v )
                    om.out.vulnerability(v.get_desc(), 
                                         severity=v.get_severity())

    def _get_and_parse(self, url):
        '''
        GET and URL that was found in the .DS_Store file, and parse it.
        
        :parameter url: The URL to GET.
        :return: None, everything is saved to self.out_queue.
        '''
        try:
            http_response = self._uri_opener.GET( url, cache=True )
        except KeyboardInterrupt, k:
            raise k
        except w3afException, w3:
            msg = ('w3afException while fetching page in crawl.ds_store, '
                   'error: %s.')
            om.out.debug( msg, (w3) )
        else:
            if not is_404( http_response ):
                self._is_vuln = True
                for fr in self._create_fuzzable_requests( http_response ):
                    self.output_queue.put(fr)

    def get_long_desc( self ):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for the .DS_Store file in all the directories and
        subdirectories that are sent as input and if it finds it will try to
        discover new URLs from its content. The .DS_Store file holds information
        about the list of files in the current directory. These files are created 
        by the Mac OS X Finder in every directory that it accesses. For example, 
        if the input is:
            - http://host.tld/w3af/index.php
            
        The plugin will perform these requests:
            - http://host.tld/w3af/.DS_Store
            - http://host.tld/.DS_Store
        
        '''

