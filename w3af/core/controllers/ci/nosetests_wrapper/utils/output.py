from __future__ import print_function

import logging
import hashlib

from itertools import ifilterfalse

from w3af.core.controllers.ci.nosetests_wrapper.constants import (NOISE,
                                                                  NOSE_IGNORE_SELECTOR)


def unique_everseen(iterable, key=None):
    """
    List unique elements, preserving order. Remember all elements ever seen.

    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    """
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in ifilterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element


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


def get_run_id(first, last):
    _first = str(first).zfill(4)
    _last = str(last).zfill(4)
    _hash = hashlib.md5('%s%s' % (first, last)).hexdigest()[:7]
    return '%s-%s-%s' % (_first, _last, _hash)


def print_status(done_list, total_tests, queued_run_ids, executor):
    msg = 'Status: (%s/%s) ' % (len(done_list), total_tests)
    logging.warning(msg)

    if len(queued_run_ids) <= 3 and queued_run_ids:
        logging.warning('The pending run ids are:')
        for qri in queued_run_ids:
            logging.warning('    - %s' % qri)

        msg = 'Running in %s threads, task queue size is %s'
        logging.warning(msg % (len(executor._threads),
                               executor._work_queue.qsize()))

    if len(done_list) > total_tests:
        raise RuntimeError('Done list has more items than total_tests!')


def print_will_fail(exit_code):
    if exit_code != 0:
        logging.critical('Build will end as failed.')


def print_summary(all_tests, run_tests, ignored_tests):
    """
    Print a summary of how many tests were run, how many are available, and
    which ones are missing.
    """
    logging.info('%s out of %s tests run' % (len(run_tests._tests),
                                             len(all_tests._tests)))
    
    missing = unique_everseen(sorted([test.id() for test in ignored_tests._tests]))
    missing_str = '\n'.join(missing)
    
    msg = 'The following %s tests were NOT run due to selector "%s":\n%s'
    logging.debug(msg % (len(ignored_tests._tests), NOSE_IGNORE_SELECTOR,
                         missing_str))


def clean_noise(output_string):
    """
    Removes useless noise from the output

    :param output_string: The output string, stdout.
    :return: A sanitized output string
    """
    for noise in NOISE:
        output_string = output_string.replace(noise + '\n', '')
        output_string = output_string.replace(noise, '')

    return output_string
