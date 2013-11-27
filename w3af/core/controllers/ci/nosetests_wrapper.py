#!/usr/bin/env python

from __future__ import print_function

import os
import re
import sys
import shlex
import select
import logging
import tempfile
import subprocess
import multiprocessing

from concurrent import futures

from utils import configure_logging


ARTIFACT_DIR = os.environ.get('CIRCLE_ARTIFACTS', '/tmp/')
LOG_FILE = os.path.join(ARTIFACT_DIR, 'nosetests.log')

MAX_WORKERS = multiprocessing.cpu_count()
NOSETESTS = 'nosetests'
# Not using code coverage (--with-cov --cov-report=xml) due to:
# https://bitbucket.org/ned/coveragepy/issue/282/coverage-combine-consumes-a-lot-of-memory
NOSE_PARAMS = '-v --with-yanc --with-doctest --doctest-tests'

# Parameters used to collect the list of tests
NOSE_COLLECT_PARAMS = '--collect-only -v --with-doctest --doctest-tests'

# TODO: Run the tests which require moth
SELECTORS = ["smoke and not internet and not moth and not root",
             "internet and not smoke and not moth and not root",
             "moth and ci_ready",]
TEST_DIRECTORIES = [
    # The order in which these are run doesn't really matter, but I do need to
    # take care of "grouping" (which directory is run) because of an incompatibility
    # between "w3af/core/ui/gui/" and "w3af/core/ui/tests/" which comes from
    # Gtk2 vs. Gtk3.
    'w3af/core/controllers/',
    'w3af/core/data/',
    
    # See https://github.com/andresriancho/w3af/issues/759
    #'w3af/core/ui/tests/',
    
    'w3af/core/ui/console/',
    'w3af/core/ui/gui/',
    'w3af/plugins/',
]

NOISE = [# Related with xvfb not having the randr extension
         'Xlib:  extension "RANDR" missing on display ":99".',
         # Related with scapy, we're not root, tcpdump is not available
         'WARNING: Failed to execute tcpdump. Check it is installed and in the PATH',
         # Warnings/log messages related with phply
         'Generating LALR tables',
         'WARNING: 2 shift/reduce conflicts',
         # Googled: only a warning related with the CV library
         'libdc1394 error: Failed to initialize libdc1394']

def open_nosetests_output(directory):
    prefix = 'nose-' + directory.replace('/', '-')
    fhandler = tempfile.NamedTemporaryFile(prefix=prefix,
                                           suffix='.log',
                                           dir=ARTIFACT_DIR,
                                           delete=False)
    
    logging.debug('nosetests output file: %s' % fhandler.name)
    
    return fhandler

def normalize_test_name(test_name):
    '''
    Tests which are generated on the fly have names like:
        foo.bar.spam(<foo.bar.spam instance at 0x837d680>,)
        
    Because of the on the fly generation, the 0x837d680 changes each time you
    collect/run the test. We don't want that, and don't care about the address
    so we replace them with 0xfffffff
    '''
    return re.sub('0x(.*?)>', '0xfffffff>', test_name.strip())

def collect_all_tests():
    '''
    :return: A list with the names of all the tests (none is run). The list
             looks like this:
             
                 ['test_plugin_desc (w3af.plugins.tests.test_basic.TestBasic)',
                  'test_found_xss (w3af.plugins.tests.output.test_csv_file.TestCSVFile)']
    '''
    cmd = '%s %s w3af/' % (NOSETESTS, NOSE_COLLECT_PARAMS)
    cmd_args = shlex.split(cmd)
    
    logging.debug('Collecting tests: "%s"' % cmd)
    
    p = subprocess.Popen(
        cmd_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        universal_newlines=True
    )

    collected_tests = ''

    # Read output while the process is alive
    while p.poll() is None:
        reads, _, _ = select.select([p.stdout, p.stderr], [], [], 1)
        for r in reads:
            collected_tests += r.read(1)
    
    p.wait()
    
    result = []
    test_name_re = re.compile('(.*?) \.\.\. ok')
    
    for line in collected_tests.splitlines():
        mo = test_name_re.match(line)
        if mo:
            result.append(normalize_test_name(mo.group(1)))
    
    logging.debug('Collected %s tests.' % len(result))
    
    result.sort()
    return result

def run_nosetests(directory, selector=None, params=NOSE_PARAMS):
    '''
    Run nosetests like this:
        nosetests $params -A $selector $directory
    
    :param directory: Which directory do we want nosetests to find tests in
    :param selector: A string with the names of the unittest tags we want to run
    :param params: The parameters to pass to nosetests
    :return: (stdout, stderr, exit code) 
    '''
    if selector is not None:
        cmd = '%s %s -A "%s" %s' % (NOSETESTS, params, selector, directory)
    else:
        cmd = '%s %s %s' % (NOSETESTS, params, directory)
        
    cmd_args = shlex.split(cmd)
    
    logging.debug('Starting: "%s"' % cmd)
    
    p = subprocess.Popen(
        cmd_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        universal_newlines=True
    )

    # Init the outputs
    output_file = open_nosetests_output(directory)
    stdout = stderr = ''
    
    # Read output while the process is alive
    while p.poll() is None:
        reads, _, _ = select.select([p.stdout, p.stderr], [], [], 1)
        for r in reads:
            # Write to the output file
            out = r.read(1)
            output_file.write(out)
            output_file.flush()
            
            # Write the output to the strings
            if r is p.stdout:
                stdout += out
            else:
                stderr += out
    
    # Close the output   
    output_file.close()
    
    logging.debug('Finished: "%s" with code "%s"' % (cmd, p.returncode))
    
    return cmd, stdout, stderr, p.returncode

def clean_noise(output_string):
    '''
    Removes useless noise from the output
    
    :param output_string: The output string, stdout.
    :return: A sanitized output string
    '''
    for noise in NOISE:
        output_string = output_string.replace(noise + '\n', '')
        output_string = output_string.replace(noise, '')
    
    return output_string

def summarize_exit_codes(exit_codes):
    '''
    Take a list of exit codes, if at least one of them is not 0, then return
    that number.
    '''
    for ec in exit_codes:
        if ec != 0: return ec
    
    return 0

def print_info_console(cmd, stdout, stderr, exit_code):
    logging.info(cmd)
    
    stdout = clean_noise(stdout)
    stderr = clean_noise(stderr)
    
    # Print to the output
    print(stdout)
    print(stderr)
    
    # Write it to the output file
    logging.debug(stdout)
    logging.debug(stderr)

def print_status(future_list, done_list):
    msg = 'Status: (%s/%s) ' % (len(done_list), len(future_list))
    logging.warning(msg)

def print_will_fail(exit_code):
    if exit_code != 0:
        logging.critical('Build will end as failed.')

def print_summary(all_tests, run_tests):
    '''
    Print a summary of how many tests were run, how many are available, and
    which ones are missing.
    '''
    logging.info('%s out of %s tests run' % (len(run_tests), len(all_tests)))
    
    missing = set(all_tests) - set(run_tests)
    missing = list(missing)
    missing.sort()
    logging.debug('The following tests were not run:\n%s' % '\n'.join(missing))
    
    # This is just to make sure we don't have crap on the run_tests list
    parsing_errors = []
    
    for test_name in run_tests:
        if test_name not in all_tests:
            parsing_errors.append(test_name)
    
    if parsing_errors:
        msg = 'Parsing error on %s tests. See log for more info.'
        logging.warning(msg % len(parsing_errors))

        issue_url = 'https://github.com/andresriancho/w3af/issues/783'
        logging.debug('Issue related with parsing errors: %s' % issue_url)        
        logging.debug('Parsing error on tests:\n%s' % '\n'.join(parsing_errors))
        #raise RuntimeError(msg % len(parsing_errors))

def get_run_tests(outputs):
    '''
    Merge all the information from the command outputs into one consolidated
    list of tests which were run.
    
    :param outputs: A list containing (stdout, stderr) for each of the
                    nosetests commands which were run.
    :return: A list with the names of the tests which were run in the same
             format as collect_all_tests to be able to compare them.
    '''
    test_name_re = re.compile('(.*?) \.\.\. .*?')
    result = []
    
    for stdout, stderr in outputs:
        for output in (stdout, stderr):
            for line in output.splitlines():
                mo = test_name_re.match(line)
                if mo:
                    result.append(normalize_test_name(mo.group(1)))
    
    result = list(set(result))
    result.sort()
    logging.debug('Run %s tests.' % len(result))
    logging.debug('The following tests were run:\n%s' % '\n'.join(result))

    return result

def nose_strategy():
    '''
    :return: A list with the tuples of (SELECTORS, TEST_DIRECTORIES) to run
             nosetests on. This basically defines which tests to run.
    '''
    for selector in SELECTORS:
        for directory in TEST_DIRECTORIES:
            yield selector, directory
            
if __name__ == '__main__':
    exit_codes = []
    future_list = []
    done_list = []
    outputs = []
    
    configure_logging(LOG_FILE)
    
    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for selector, directory in nose_strategy():
            args = run_nosetests, directory, selector, NOSE_PARAMS
            future_list.append(executor.submit(*args))
        
        print_status(future_list, done_list)
        
        for future in futures.as_completed(future_list):
            cmd, stdout, stderr, exit_code = future.result()
            exit_codes.append(exit_code)
            done_list.append(future)
            outputs.append((stdout, stderr))
            
            print_info_console(cmd, stdout, stderr, exit_code)
            print_will_fail(exit_code)
            print_status(future_list, done_list)
    
    all_tests = collect_all_tests()
    run_tests = get_run_tests(outputs)
    print_summary(all_tests, run_tests) 
        
    # We need to set the exit code.
    sys.exit(summarize_exit_codes(exit_codes))
