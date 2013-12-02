#!/usr/bin/env python

from __future__ import print_function

import sys
import os

# Need this hack in order to be able to re-add the current path to the
# python-path, since running a script seems to change it (?)
sys.path.insert(0, os.path.abspath(os.curdir))

from concurrent import futures

from w3af.core.controllers.ci.utils import configure_logging
from w3af.core.controllers.ci.nosetests_wrapper.utils.nosetests import run_nosetests
from w3af.core.controllers.ci.nosetests_wrapper.utils.test_stats import (get_all_tests,
                                                                         get_run_tests,
                                                                         get_ignored_tests)
from w3af.core.controllers.ci.nosetests_wrapper.constants import (LOG_FILE,
                                                                  MAX_WORKERS,
                                                                  TEST_DIRECTORIES,
                                                                  NOSETESTS, NOSE_PARAMS,
                                                                  NOSE_RUN_SELECTOR)
from w3af.core.controllers.ci.nosetests_wrapper.utils.output import (print_info_console,
                                                                     print_status,
                                                                     print_will_fail,
                                                                     print_summary)

def summarize_exit_codes(exit_codes):
    '''
    Take a list of exit codes, if at least one of them is not 0, then return
    that number.
    '''
    for ec in exit_codes:
        if ec != 0: return ec
    
    return 0

def nose_strategy():
    '''
    :return: A list with the nosetests commands to run.
    '''
    for directory in TEST_DIRECTORIES:
        cmd = '%s %s -A "%s" %s' % (NOSETESTS, NOSE_PARAMS, NOSE_RUN_SELECTOR,
                                    directory)
        yield cmd
            
if __name__ == '__main__':
    exit_codes = []
    future_list = []
    done_list = []
    
    configure_logging(LOG_FILE)
    
    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for nose_cmd in nose_strategy():
            args = run_nosetests, nose_cmd
            future_list.append(executor.submit(*args))
        
        total_tests = len(future_list)
        print_status(done_list, total_tests)
        
        while future_list:
            try:
                for future in futures.as_completed(future_list, timeout=120):
                    cmd, stdout, stderr, exit_code = future.result()
                    exit_codes.append(exit_code)
                    done_list.append(future)
                    
                    print_info_console(cmd, stdout, stderr, exit_code)
                    print_will_fail(exit_code)
                    print_status(done_list, total_tests)
            except futures.TimeoutError:
                print_status(done_list, total_tests)
            
            # Filter future_list to avoid issues with tasks which are already
            # finished/done
            future_list = [f for f in future_list if f not in done_list]
                
    all_tests = get_all_tests()
    run_tests = get_run_tests()
    ignored_tests = get_ignored_tests()
    print_summary(all_tests, run_tests, ignored_tests) 
        
    # We need to set the exit code.
    sys.exit(summarize_exit_codes(exit_codes))
