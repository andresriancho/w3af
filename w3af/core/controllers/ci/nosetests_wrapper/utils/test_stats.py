'''
collect_tests.py

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
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
'''
import os
import shlex
import logging
import subprocess

from xunit import parse_xunit
from xunit import normalize_test_names

from w3af.core.controllers.ci.nosetests_wrapper.constants import (ARTIFACT_DIR,
                                                                  NOSETESTS,
                                                                  NOSE_COLLECT_PARAMS,
                                                                  NOSE_XUNIT_EXT,
                                                                  NOSE_OUTPUT_PREFIX,
                                                                  NOSE_IGNORE_SELECTOR)

def _get_tests(fname, selector=None):
    '''
    Collect tests and return them.
    
    :param fname: The tests will be written to fname in xunit format 
    :param selector: Tests are filtered based on selector
    :return: A test suite as returned by xunitparser with all the tests available
             in the w3af framework source code, without any selectors.
    '''
    output_file = os.path.join(ARTIFACT_DIR, fname)
    collect_with_output = NOSE_COLLECT_PARAMS % output_file
    
    if selector is not None:
        cmd = '%s %s -A "%s" w3af/' % (NOSETESTS, collect_with_output,
                                       selector)
    else:
        cmd = '%s %s w3af/' % (NOSETESTS, collect_with_output)
    
    cmd_args = shlex.split(cmd)
    
    logging.debug('Collecting tests: "%s"' % cmd)
    subprocess.check_call(cmd_args)

    test_suite, test_result = parse_xunit(output_file)
    
    normalize_test_names(test_suite)
    
    logging.debug('Collected %s tests.' % len(test_result.testsRun))
    
    return test_suite

def get_all_tests():
    '''
    Collect all tests and return them
    
    :return: A test suite as returned by xunitparser with all the tests available
             in the w3af framework source code, without any selectors.
    '''
    return _get_tests('all.xml')

def get_ignored_tests():
    '''
    Collect all ignored tests and return them
    
    :return: A test suite as returned by xunitparser with all the tests available
             in the w3af framework source code, without any selectors.
    '''
    return _get_tests('ignored.xml', NOSE_IGNORE_SELECTOR)

def get_run_tests():
    '''
    Merge all the information from the command outputs into one consolidated
    test suite which contains all tests which were run.
    
    :return: A list with the names of the tests which were run in the same
             format as collect_all_tests to be able to compare them.
    '''
    test_suite = None
    msg_fmt = 'Reading %s run tests from: "%s"'
    
    for fname in os.listdir(ARTIFACT_DIR):
        if fname.startswith(NOSE_OUTPUT_PREFIX) and \
        fname.endswith(NOSE_XUNIT_EXT):
            
            curr_test_suite, test_result = parse_xunit(fname)
            logging.debug(msg_fmt % (test_result.testsRun, fname))
            
            # Merge all the tests.
            if test_suite is None:
                test_suite = curr_test_suite
            else:
                for test in curr_test_suite:
                    test_suite.addTest(test)
    
    normalize_test_names(test_suite)
    
    run_str = '\n'.join(sorted([t.id() for t in test_suite._tests]))
    
    logging.debug('Run %s tests.' % len(test_suite._tests))
    logging.debug('The following tests were run:\n%s' % run_str)

    return test_suite