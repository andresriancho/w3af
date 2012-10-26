'''
web_diff.py

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
from core.data.options.option_list import OptionList

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
from core.data.parsers.url import URL
from core.controllers.core_helpers.fingerprint_404 import is_404

import os


class web_diff(CrawlPlugin):
    '''
    Compare a local directory with a remote URL path.
    
    @author: Andres Riancho (andres.riancho@gmail.com)  
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # Internal variables
        self._run = True
        self._first = True
        self._start_path = None
        
        self._fuzzable_requests = []
        self._not_eq = []
        self._not_eq_content = []
        self._eq = []
        self._eq_content = []
        
        # Configuration
        self._ban_url = ['asp', 'jsp', 'php']
        self._content = True
        self._local_dir = ''
        self._remote_path = ''
        
    def crawl(self, fuzzable_request ):
        '''
        GET's local files one by one until done.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains (among other things) the URL to test.
        '''
        if not self._run:
            # This will remove the plugin from the crawl plugins to be run.
            raise w3afRunOnce()
        else:
            self._run = False
                    
            if self._local_dir != '' and self._remote_path:
                os.path.walk( self._local_dir, self._compare_dir, None )
                self._generate_report()
                return self._fuzzable_requests
            else:
                msg = 'web_diff plugin: You have to configure the local and remote directory'
                msg += ' to compare.'
                raise w3afException( msg )
        return []
    
    def _generate_report( self ):
        '''
        Generates a report based on:
            - self._not_eq
            - self._not_eq_content
            - self._eq
            - self._eq_content
        '''
        if len( self._eq ):
            msg = 'The following files exist in the local directory and in the remote server:'
            om.out.information( msg )
            for file_name in self._eq:
                om.out.information('- '+ file_name)
        
        if len( self._eq_content ):
            msg = 'The following files exist in the local directory and in the remote server'
            msg += ' and their contents match:'
            om.out.information(msg)
            for file_name in self._eq_content:
                om.out.information('- '+ file_name)

        if len( self._not_eq ):
            msg = 'The following files exist in the local directory and NOT in the remote server:'
            om.out.information(msg)
            for file_name in self._not_eq:
                om.out.information('- '+ file_name)
        
        if len( self._not_eq_content ):
            msg = 'The following files exist in the local directory and in the remote server but'
            msg += ' their contents dont match:'
            om.out.information(msg)
            for file_name in self._not_eq_content:
                om.out.information('- '+ file_name)
                
        file_stats = str(len(self._eq)) + ' of ' + str( len(self._eq) + len(self._not_eq) )
        content_stats = str(len(self._eq_content)) + ' of '
        content_stats += str( len(self._eq_content) + len(self._not_eq_content) )
        om.out.information('Match files: ' + file_stats )
        om.out.information('Match contents: ' + content_stats )

    def _compare_dir( self, arg, directory, flist ):
        '''
        This function is the callback function called from os.path.walk, from the python
        help function:
        
        walk(top, func, arg)
            Directory tree walk with callback function.
        
            For each directory in the directory tree rooted at top (including top
            itself, but excluding '.' and '..'), call func(arg, dirname, fnames).
            dirname is the name of the directory, and fnames a list of the names of
            the files and subdirectories in dirname (excluding '.' and '..').  func
            may modify the fnames list in-place (e.g. via del or slice assignment),
            and walk will only recurse into the subdirectories whose names remain in
            fnames; this can be used to implement a filter, or to impose a specific
            order of visiting.  No semantics are defined for, or required of, arg,
            beyond that arg is always passed to func.  It can be used, e.g., to pass
            a filename pattern, or a mutable object designed to accumulate
            statistics.  Passing None for arg is common.

        '''
        if self._first:
            self._start_path = directory
            self._first = False
        
        directory_2 = directory.replace( self._start_path,'' )
        path = self._remote_path
        if directory_2 != '':
            path += directory_2 + os.path.sep
        else:
            path += directory_2
        
        for fname in flist:
            if os.path.isfile( directory + os.path.sep + fname ):
                url = path.urlJoin( fname )
                response = self._easy_GET( url )
            
                if not is_404( response ):
                    if response.is_text_or_html():
                        for fr in self._create_fuzzable_requests( response ):
                            self.output_queue.put(fr)
                    self._check_content( response, directory + os.path.sep + fname )
                    self._eq.append( url )
                else:
                    self._not_eq.append( url )
        
    def _check_content( self, response, file_name ):
        '''
        Check if the contents match.
        '''
        if self._content:
            if file_name.count('.'):
                extension = os.path.splitext( file_name )[1].replace('.', '')
                
                if extension not in self._ban_url:
                    try:
                        fd = open( file_name, 'r' )
                    except:
                        om.out.debug('Failed to open file: ' + file_name)
                    else:
                        if fd.read() == response.getBody():
                            self._eq_content.append( response.getURL() )
                        else:
                            self._not_eq_content.append( response.getURL() )
                            
                        fd.close()
        
    def _easy_GET( self, url ):
        '''
        A GET wrapper.
        
        @return: The HTTPResponse object.
        '''
        response = None
        try:
            response = self._uri_opener.GET( url, cache=True )
        except KeyboardInterrupt,e:
            raise e
        else:
            return response
    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'When comparing, also compare the content of files.'
        o1 = option('content', self._content, d1, 'boolean')
        
        d2 = 'The local directory used in the comparison.'
        o2 = option('localDir', self._local_dir, d2, 'string')

        d3 = 'The remote directory used in the comparison.'
        o3 = option('remotePath', self._remote_path, d3, 'string')

        d4 = 'When comparing content of two files, ignore files with these extensions.'
        o4 = option('banUrl', self._ban_url, d4, 'list')
        
        ol = OptionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        return ol

    def set_options( self, options_list ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter options_list: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._content = options_list['content'].getValue()
        self._ban_url = options_list['banUrl'].getValue()
        self._local_dir = options_list['localDir'].getValue()
        try:
            url = URL(options_list['remotePath'].getValue())
            self._remote_path = url.getDomainPath()
        except ValueError:
            pass

    def get_plugin_deps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return [ ]

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to do a diff of two directories, a local and a remote one. The idea is to 
        mimic the functionality implemented by the linux command "diff" when invoked with two
        directories.
        
        Four configurable parameter exist:
            - localDir
            - remotePath
            - banUrl
            - content
            
        This plugin will read the file list inside "localDir", and for each file it will request the 
        same filename from the "remotePath", matches and failures are recorded and saved.
        The content of both files is checked only if "content" is set to True and the file
        extension aint in the "banUrl" list.
        
        The "banUrl" list should be used to ban script extensions like ASP, PHP, etc.
        '''
