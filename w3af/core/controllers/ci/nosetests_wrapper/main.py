#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import time
import logging

# Need this hack in order to be able to re-add the current path to the
# python-path, since running a script seems to change it (?)
sys.path.insert(0, os.path.abspath(os.curdir))

from concurrent import futures

from w3af.core.controllers.ci.utils import configure_logging
from w3af.core.controllers.ci.nosetests_wrapper.utils.nosetests import run_nosetests
from w3af.core.controllers.ci.nosetests_wrapper.utils.test_stats import (get_all_tests,
                                                                         get_run_tests,
                                                                         get_test_ids,
                                                                         save_noseids_as_json,
                                                                         get_ignored_tests)
from w3af.core.controllers.ci.nosetests_wrapper.constants import (LOG_FILE,
                                                                  MAX_WORKERS,
                                                                  NOSETESTS, NOSE_PARAMS,
                                                                  NOSE_RUN_SELECTOR,
                                                                  CHUNK_SIZE)
from w3af.core.controllers.ci.nosetests_wrapper.utils.output import (print_info_console,
                                                                     print_status,
                                                                     print_will_fail,
                                                                     print_summary,
                                                                     get_run_id)


def summarize_exit_codes(exit_codes):
    """
    Take a list of exit codes, if at least one of them is not 0, then return
    that number.
    """
    for ec in exit_codes:
        if ec != 0:
            return ec
    
    return 0


def nose_strategy():
    """
    :return: A list with the nosetests commands to run.
    """
    test_ids = get_test_ids(NOSE_RUN_SELECTOR)
    save_noseids_as_json()
    
    for tests_to_run in zip(*[iter(test_ids)]*CHUNK_SIZE):
        
        first = tests_to_run[0]
        last = tests_to_run[-1]
        
        tests_str = ' '.join([str(i) for i in tests_to_run])
        cmd = '%s %s %s' % (NOSETESTS, NOSE_PARAMS, tests_str)
        
        yield cmd, first, last


if __name__ == '__main__':
    exit_codes = []
    future_list = []
    done_list = []
    queued_run_ids = []
    start_time = time.time()

    configure_logging(LOG_FILE)

    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for nose_cmd, first, last in nose_strategy():
            args = run_nosetests, nose_cmd, first, last

            run_id = get_run_id(first, last)
            queued_run_ids.append(run_id)

            future = executor.submit(*args)
            future.run_id = run_id
            future_list.append(future)
        
        total_tests = len(future_list)
        print_status(start_time, done_list, total_tests, queued_run_ids,
                     executor, exit_codes)
        
        while future_list:
            try:
                for future in futures.as_completed(future_list, timeout=120):
                    try:
                        cmd, stdout, stderr, exit_code, output_fname = future.result()
                    except Exception as e:
                        msg = 'Run id %s raised exception: "%s"'
                        logging.error(msg % (future.run_id, e))
                        print_will_fail(1)
                        raise
                    else:
                        exit_codes.append(exit_code)
                        done_list.append(future)
                        queued_run_ids.remove(future.run_id)

                        print_status(start_time, done_list, total_tests,
                                     queued_run_ids, executor, exit_codes)

                        if exit_code != 0:
                            print_info_console(cmd, stdout, stderr,
                                               exit_code, output_fname)
                            print_will_fail(exit_code)
                    
            except futures.TimeoutError:
                logging.debug('Hit futures.as_completed timeout.')
                logging.warning('Waiting...')
                print_status(start_time, done_list, total_tests, queued_run_ids,
                             executor, exit_codes)
            
            # Filter future_list to avoid issues with tasks which are already
            # finished/done
            future_list = [f for f in future_list if f not in done_list]

    all_tests = get_all_tests()
    run_tests = get_run_tests()
    ignored_tests = get_ignored_tests()
    print_summary(all_tests, run_tests, ignored_tests) 
        
    # We need to set the exit code.
    sys.exit(summarize_exit_codes(exit_codes))
