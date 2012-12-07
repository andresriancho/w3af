'''
sqlmap_wrapper.py

Copyright 2012 Andres Riancho

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
import os
import shlex
import subprocess

from core.data.parsers.url import URL


class SQLMapWrapper(object):
    
    SQLMAP_LOCATION = os.path.join('plugins', 'attack', 'db', 'sqlmap') 
    
    VULN_STR = 'sqlmap identified the following injection points'
    NOT_VULN_STR = 'all tested parameters appear to be not injectable'
    
    def __init__(self, target, coloring=False):
        if not isinstance(target, Target):
            fmt = 'Invalid type %s for target parameter in SQLMapWrapper ctor.'
            raise TypeError(fmt % type(target))

        self.target = target
        self.coloring = coloring
        self.local_proxy_url = None
        self.last_command = None
        self.verified_vulnerable = False
    
    def is_vulnerable(self):
        '''
        @return: True if the URL is vulnerable to SQL injection.
        '''
        if self.verified_vulnerable:
            return self.verified_vulnerable
        
        params = ['--batch',]
        
        full_command, stdout, stderr = self.run_sqlmap(params)
                
        if self.VULN_STR in stdout and self.NOT_VULN_STR not in stdout:
            self.verified_vulnerable = True
            return True
        
        if self.NOT_VULN_STR in stdout and self.VULN_STR not in stdout:
            return False 
        
        fmt = 'Unexpected answer found in sqlmap output for command "%s".'
        raise NotImplementedError(fmt % full_command)
    
    def _run(self, custom_params):
        '''
        Internal function used by run_sqlmap and run_sqlmap_with_pipes to
        call subprocess.
        
        @return: A Popen object.
        '''
        final_params = self.get_wrapper_params(custom_params)
        target_params = self.target.to_params()
        all_params = ['python', 'sqlmap.py'] + final_params + target_params
        
        process = subprocess.Popen(args=all_params,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=False,
                                   universal_newlines=True,
                                   cwd=self.SQLMAP_LOCATION)
        
        full_command = ' '.join(all_params)
        self.last_command = full_command
        
        return process
    
    def run_sqlmap(self, custom_params):
        '''
        Run sqlmap and wait for it to finish before getting its output.
        
        @param custom_params: A list with the extra parameters that we want to
                              send to sqlmap.
                              
        @return: Runs sqlmap and returns a tuple containing:
                    (the command was run,
                     stdout for the command,
                     stderr for the command)
        '''
        process = self._run(custom_params)
        stdout, stderr = process.communicate()                
        return self.last_command, stdout, stderr
        
    def run_sqlmap_with_pipes(self, custom_params):
        '''
        Run sqlmap and immediately return handlers to stdout, stderr and stdin
        so the code using this can interact directly with the process.
        
        @param custom_params: A list with the extra parameters that we want to
                              send to sqlmap.
                              
        @return: Runs sqlmap and returns a tuple with:
                    (last command run,
                     file-like object for stdout,
                     file-like object for stderr,
                     file-like object for stdin)
                 
                 This is very useful for using with w3af's output manager.
        '''
        process = self._run(custom_params)
        return self.last_command, process.stdout, process.stderr, process.stdin
    
    def direct(self, params_str):
        extra_params = shlex.split(params_str)
        return self.run_sqlmap_with_pipes(extra_params)
    
    def get_wrapper_params(self, extra_params=[]):
        params = []
        
        if not self.coloring:
            params.append('--disable-coloring')
        
        if self.local_proxy_url is not None:
            params.append('--proxy=%s' % self.local_proxy_url)
        
        params.extend(extra_params)
        
        return params
    
    def _wrap_param(self, custom_params):
        '''
        Utility function to allow me to easily wrap params.
        
        @return: Runs sqlmap with --dbs and returns a tuple with:
                    (last command run,
                     file-like object for stdout,
                     file-like object for stderr,
                     file-like object for stdin)
        '''
        process = self._run(custom_params)
        return (self.last_command, process.stdout,
                process.stderr, process.stdin)
        
    def dbs(self):
        return self._wrap_param(['--dbs',])

    def tables(self):
        return self._wrap_param(['--tables',])

    def users(self):
        return self._wrap_param(['--users',])

    def dump(self):
        return self._wrap_param(['--dump',])
        
class Target(object):
    def __init__(self, uri, post_data=None):
        if not isinstance(uri, URL):
            fmt = 'Invalid type %s for uri parameter in Target ctor.'
            raise TypeError(fmt % type(uri))

        if post_data is not None and not isinstance(post_data, basestring):
            fmt = 'Invalid type %s for post_data parameter in Target ctor.'
            raise TypeError(fmt % type(post_data))
        
        self.uri = uri
        self.post_data = post_data
    
    def to_params(self):
        params = []
        params.append("--url=%s" % self.uri)
        
        if self.post_data is not None:
            params.append("--data=%s" % self.post_data)
        
        return params