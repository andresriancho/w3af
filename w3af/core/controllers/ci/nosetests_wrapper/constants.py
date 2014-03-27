import os
import multiprocessing


ARTIFACT_DIR = os.environ.get('CIRCLE_ARTIFACTS', '/tmp/')
LOG_FILE = os.path.join(ARTIFACT_DIR, 'nosetests.log')

# How many nosetests commands to run at the same time
MAX_WORKERS = multiprocessing.cpu_count()
# How many tests to send to each process
CHUNK_SIZE = 25

# Where the test ids will be stored
ID_FILE = os.path.join(ARTIFACT_DIR, 'noseids.pickle')

NOSETESTS = 'nosetests'
# Not using code coverage (--with-cov --cov-report=xml) due to:
# https://bitbucket.org/ned/coveragepy/issue/282/coverage-combine-consumes-a-lot-of-memory
NOSE_PARAMS = '--with-yanc --with-doctest --doctest-tests --with-xunit'\
              ' -v --xunit-file=%%s --with-id --id-file=%s' % ID_FILE
# One test can't run for more than this amount of seconds
NOSE_TIMEOUT = 360

# Parameters used to collect the list of tests
NOSE_COLLECT_PARAMS = '--with-id --collect-only --with-doctest'\
                      ' --doctest-tests --with-xunit --xunit-file=%%s'\
                      ' --id-file=%s' % ID_FILE
NOSE_COLLECT_IGNORE_PARAMS = '--with-id --collect-only --with-xunit'\
                             ' --xunit-file=%%s --id-file=%s' % ID_FILE

NOSE_OUTPUT_PREFIX = 'nose'
NOSE_XUNIT_EXT = 'xml'
NOSE_RUN_SELECTOR = 'not ci_fails and not fails'
NOSE_IGNORE_SELECTOR = 'ci_fails or fails'

NOISE = [# Related with xvfb not having the randr extension
         'Xlib:  extension "RANDR" missing on display ":99".',
         # Related with scapy, we're not root, tcpdump is not available
         'WARNING: Failed to execute tcpdump. Check it is installed and in the PATH',
         # Warnings/log messages related with phply
         'Generating LALR tables',
         'WARNING: 2 shift/reduce conflicts',
         # Googled: only a warning related with the CV library
         'libdc1394 error: Failed to initialize libdc1394']
