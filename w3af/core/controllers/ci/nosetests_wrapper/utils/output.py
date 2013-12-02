from __future__ import print_function

import logging

from w3af.core.controllers.ci.nosetests_wrapper.utils.nosetests import clean_noise
from w3af.core.controllers.ci.nosetests_wrapper.constants import NOSE_IGNORE_SELECTOR


def print_info_console(cmd, stdout, stderr, exit_code, output_fname):
    fmt = '%s (%s)'
    logging.info(fmt % (cmd, output_fname))
    
    stdout = clean_noise(stdout)
    stderr = clean_noise(stderr)
    
    # Print to the output
    print(stdout)
    print(stderr)
    
    # Write it to the output file
    logging.debug(stdout)
    logging.debug(stderr)

def print_status(done_list, total_tests):
    msg = 'Status: (%s/%s) ' % (len(done_list), total_tests)
    logging.warning(msg)
    
    if len(done_list) > total_tests:
        raise RuntimeError('Done list has more items than total_tests!')

def print_will_fail(exit_code):
    if exit_code != 0:
        logging.critical('Build will end as failed.')

def print_summary(all_tests, run_tests, ignored_tests):
    '''
    Print a summary of how many tests were run, how many are available, and
    which ones are missing.
    '''
    logging.info('%s out of %s tests run' % (len(run_tests._tests),
                                             len(all_tests._tests)))
    
    missing = sorted([test.id() for test in ignored_tests._tests])
    missing_str = '\n'.join(missing)
    
    msg = 'The following tests were not run due to selector "%s":\n%s'
    logging.debug(msg % (NOSE_IGNORE_SELECTOR, missing_str))
    