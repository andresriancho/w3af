#!/usr/bin/env python

import sys
import shlex
import subprocess

NOSETESTS = 'nosetests'
NOSE_PARAMS = '--with-doctest --doctest-tests'
SELECTORS = ["smoke and not internet and not moth and not root",]
TEST_DIRECTORIES = [
    # The order in which these are run doesn't really matter, but I do need to
    # take care of "grouping" (which directory is run) because of an incompatibility
    # between "w3af/core/ui/gui/" and "w3af/core/ui/tests/" which comes from
    # Gtk2 vs. Gtk3.
    'w3af/core/controllers/',
    'w3af/core/data/',
    'w3af/core/ui/tests/',
    'w3af/core/ui/console/',
    'w3af/core/ui/gui/',
    'w3af/plugins/',
]

def run_nosetests(selector, directory, params=NOSE_PARAMS):
    '''
    Run nosetests like this:
        nosetests $params -A $selector $directory
    
    :param selector: A string with the names of the unittest tags we want to run
    :param directory: Which directory do we want nosetests to find tests in
    :param params: The parameters to pass to nosetests
    :return: (stdout, stderr, exit code) 
    '''
    cmd = '%s %s -A "%s" %s' % (NOSETESTS, params, selector, directory)
    cmd_args = shlex.split(cmd)
    
    p = subprocess.Popen(
        cmd_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        universal_newlines=True
    )
    stdout, stderr = p.communicate()
    
    print stdout
    print stderr
    
    return p.stdout, p.stderr, p.returncode


def run_selector(selector, params=NOSE_PARAMS):
    '''
    Run nosetests on all the TEST_DIRECTORIES using the selector and params.
    
    :param selector: A string with the names of the unittest tags we want to run
    :param params: The parameters to pass to nosetests
    '''
    exit_codes = []
    
    for directory in TEST_DIRECTORIES:
        stdout, stderr, exit_code = run_nosetests(selector, directory, params)
        exit_codes.append(exit_code)
        
    return summarize_exit_codes(exit_codes)

def summarize_exit_codes(exit_codes):
    '''
    Take a list of exit codes, if at least one of them is not 0, then return
    that number.
    '''
    for ec in exit_codes:
        if ec != 0: return ec
    
    return 0

if __name__ == '__main__':
    selector_exit_codes = []
    
    for selector in SELECTORS:
        selector_exit_code = run_selector(selector)
        selector_exit_codes.append(selector_exit_code)
            
    # TODO: Run the tests which require moth

    # We need to set the exit code.
    sys.exit(summarize_exit_codes(selector_exit_codes))