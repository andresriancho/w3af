"""
sqlmap_wrapper.py

Copyright 2012 Andres Riancho

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
import os
import re
import shlex
import subprocess

from w3af import ROOT_PATH
from w3af.core.data.parsers.url import URL
from w3af.core.controllers.daemons.proxy import Proxy


class SQLMapWrapper(object):
    
    DEBUG_ARGS = ['-v6']
    SQLMAP_LOCATION = os.path.join(ROOT_PATH, 'plugins', 'attack', 'db', 'sqlmap') 
    VULN_STR = 'sqlmap identified the following injection points'
    NOT_VULN_STR = 'all tested parameters appear to be not injectable'

    SQLMAP_ERRORS = ('connection timed out to the target',
                     'infinite redirect loop detected',
                     'it is not recommended to continue in this kind of cases',
                     'unable to connect to the target url or proxy',
                     "[INFO] skipping '")
    
    def __init__(self, target, uri_opener, coloring=False, debug=False):
        if not isinstance(target, Target):
            fmt = 'Invalid type %s for target parameter in SQLMapWrapper ctor.'
            raise TypeError(fmt % type(target))

        self._start_proxy(uri_opener)

        self.debug = debug
        self.target = target
        self.coloring = coloring
        self.last_command = None
        self.verified_vulnerable = False
    
    def _start_proxy(self, uri_opener):
        """
        Saves the proxy configuration to self.local_proxy_url in order for the
        wrapper to use it in the calls to sqlmap.py and have the traffic go
        through our proxy (which has the user configuration, logging, etc).
        
        :return: None, an exception is raised if something fails.
        """
        host = '127.0.0.1'
        
        self.proxy = Proxy(host, 0, uri_opener)
        self.proxy.start()
        self.local_proxy_url = 'http://%s:%s/' % (host, self.proxy.get_bind_port())
    
    def cleanup(self):
        self.proxy.stop()
    
    def is_vulnerable(self):
        """
        :return: True if the URL is vulnerable to SQL injection.
        """
        if self.verified_vulnerable:
            return self.verified_vulnerable
        
        params = ['--batch',]
        
        full_command, stdout, stderr = self.run_sqlmap(params)
                
        if self.VULN_STR in stdout and self.NOT_VULN_STR not in stdout:
            self.verified_vulnerable = True
            return True
        
        if self.NOT_VULN_STR in stdout and self.VULN_STR not in stdout:
            return False 

        for error_string in self.SQLMAP_ERRORS:
            if error_string in stdout:
                # We found an unknown sqlmap error, such as a timeout
                return False
        
        fmt = 'Unexpected answer found in sqlmap output for command "%s": "%s"'
        raise NotImplementedError(fmt % (full_command, stdout))
    
    def _run(self, custom_params):
        """
        Internal function used by run_sqlmap and run_sqlmap_with_pipes to
        call subprocess.
        
        :return: A Popen object.
        """
        final_params = self.get_wrapper_params(custom_params)
        target_params = self.target.to_params()
        all_params = ['python', 'sqlmap.py'] + final_params + target_params

        if self.debug:
            all_params += self.DEBUG_ARGS

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
        """
        Run sqlmap and wait for it to finish before getting its output.
        
        :param custom_params: A list with the extra parameters that we want to
                              send to sqlmap.
                              
        :return: Runs sqlmap and returns a tuple containing:
                    (last command run,
                     stdout, sterr)
        """
        process = self._run(custom_params)
        self.last_stdout, self.last_stderr = process.communicate()
        return self.last_command, self.last_stdout, self.last_stderr
        
    def run_sqlmap_with_pipes(self, custom_params):
        """
        Run sqlmap and immediately return handlers to stdout, stderr and stdin
        so the code using this can interact directly with the process.
        
        :param custom_params: A list with the extra parameters that we want to
                              send to sqlmap.
                              
        :return: Runs sqlmap and returns a tuple with:
                    (last command run,
                     Popen object so that everyone can read .stdout)
                 
                 This is very useful for using with w3af's output manager.
        """
        process = self._run(custom_params)
        return self.last_command, process
    
    def direct(self, params):
        
        if isinstance(params, basestring):
            extra_params = shlex.split(params)
            
        return self.run_sqlmap_with_pipes(extra_params)
    
    def get_wrapper_params(self, extra_params=[]):
        params = []
        
        # TODO: This one will dissapear the day I add stdin handling support
        #       for the wrapper. Please remember that this support will have to
        #       take care of stdin and all other inputs from other UIs
        params.append('--batch')
        
        if not self.coloring:
            params.append('--disable-coloring')
        
        if self.local_proxy_url is not None:
            params.append('--proxy=%s' % self.local_proxy_url)
        
        params.extend(extra_params)
        
        return params
    
    def _wrap_param(self, custom_params):
        """
        Utility function to allow me to easily wrap params.
        
        :return: Runs sqlmap with --dbs and returns a tuple with:
                    (last command run,
                     Popen object so that everyone can read .stdout,
                     .stderr, .stdin attributes)
        """
        process = self._run(custom_params)
        return self.last_command, process
        
    def dbs(self):
        return self._wrap_param(['--dbs',])

    def tables(self):
        return self._wrap_param(['--tables',])

    def users(self):
        return self._wrap_param(['--users',])

    def dump(self):
        return self._wrap_param(['--dump',])

    def read(self, filename):
        """
        :param filename: The file to be read
        :return: The contents of the file that was passed as parameter
        """
        cmd, process = self._wrap_param(['--file-read=%s' % filename,])
        local_file_re = re.compile("the local file (.*?) and")
        # pylint: disable=E1101
        stdout = process.stdout.read()
        
        try:
            local_file = local_file_re.search(stdout).group(1)
        except:
            # FIXME: I'll have to fix this at some point... files that do not
            # exist should raise an exception (or something similar), instead
            # of just returning an empty string. This is a big FAIL from my
            # initial design of the payloads/shell API.
            return ''
        else:
            if os.path.exists(local_file):
                return file(local_file).read()
        
        return 


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
    
    def __repr__(self):
        return '<Target %s %s>' % (self.uri, self.post_data)