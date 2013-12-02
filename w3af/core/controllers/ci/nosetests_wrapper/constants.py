import os
import multiprocessing


ARTIFACT_DIR = os.environ.get('CIRCLE_ARTIFACTS', '/tmp/')
LOG_FILE = os.path.join(ARTIFACT_DIR, 'nosetests.log')

MAX_WORKERS = multiprocessing.cpu_count()
NOSETESTS = 'nosetests'
# Not using code coverage (--with-cov --cov-report=xml) due to:
# https://bitbucket.org/ned/coveragepy/issue/282/coverage-combine-consumes-a-lot-of-memory
NOSE_PARAMS = '-v --with-yanc --with-doctest --doctest-tests --with-xunit --xunit-file=%s'
# One test can't run for more than this amount of seconds
NOSE_TIMEOUT = 20

# Parameters used to collect the list of tests
NOSE_COLLECT_PARAMS = '--collect-only -v --with-doctest --doctest-tests --with-xunit --xunit-file=%s'

NOSE_OUTPUT_PREFIX = 'nose-'
NOSE_XUNIT_EXT = '.xml'
NOSE_RUN_SELECTOR = 'not ci_fails and not fails'
NOSE_IGNORE_SELECTOR = 'ci_fails or fails'

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

    'w3af/plugins/audit/',
    'w3af/plugins/attack/',
    'w3af/plugins/auth/',
    'w3af/plugins/bruteforce/',
    'w3af/plugins/crawl/',
    'w3af/plugins/evasion/',
    'w3af/plugins/grep/',
    'w3af/plugins/infrastructure/',
    'w3af/plugins/mangle/',
    'w3af/plugins/output/',
    
    'w3af/plugins/tests/audit/',
    'w3af/plugins/tests/attack/',
    'w3af/plugins/tests/auth/',
    'w3af/plugins/tests/bruteforce/',
    'w3af/plugins/tests/crawl/',
    'w3af/plugins/tests/evasion/',
    'w3af/plugins/tests/grep/',
    'w3af/plugins/tests/infrastructure/',
    'w3af/plugins/tests/mangle/',
    'w3af/plugins/tests/output/',
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
