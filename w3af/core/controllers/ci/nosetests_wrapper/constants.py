import os
import multiprocessing

from w3af.core.controllers.ci.detect import is_running_on_ci


ARTIFACT_DIR = os.environ.get('CIRCLE_ARTIFACTS', '/tmp/')
LOG_FILE = os.path.join(ARTIFACT_DIR, 'nosetests.log')

# How many nosetests commands to run at the same time
#
# At CircleCI I've got 32 cores to use, but don't want to use them all with
# nosetests (other important stuff like docker is running too), so I set a fixed
# value
if is_running_on_ci():
    MAX_WORKERS = 10
else:
    MAX_WORKERS = max(multiprocessing.cpu_count() - 1, 2)

# How many tests to send to each process
#
# Usually lower numbers are better here. A high chunk size will usually lead to
# larger delays.
CHUNK_SIZE = 3

# Where the test ids will be stored
ID_FILE = os.path.join(ARTIFACT_DIR, 'noseids.pickle')
JSON_ID_FILE = os.path.join(ARTIFACT_DIR, 'noseids.json')

NOSETESTS = 'nosetests'

# Not using code coverage (--with-cov --cov-report=xml) due to:
# https://bitbucket.org/ned/coveragepy/issue/282/
NOSE_PARAMS = ('--with-timer --with-doctest --doctest-tests --with-xunit'
               ' -v --xunit-file=%%s --with-id --id-file=%s' % ID_FILE)

# One test can't run for more than this amount of seconds
NOSE_TIMEOUT = 60 * 10

# Parameters used to collect the list of tests
NOSE_COLLECT_PARAMS = ('--with-id --collect-only --with-xunit --xunit-file=%%s'
                       ' --id-file=%s' % ID_FILE)
NOSE_COLLECT_IGNORE_PARAMS = ('--with-id --collect-only --with-xunit'
                              ' --xunit-file=%%s --id-file=%s' % ID_FILE)

NOSE_OUTPUT_PREFIX = 'nose'
NOSE_XUNIT_EXT = 'xml'
NOSE_RUN_SELECTOR = 'not ci_fails and not fails and not ci_ignore'
NOSE_IGNORE_SELECTOR = 'ci_fails or fails or ci_ignore'

NOISE = [
         # Related with xvfb not having the randr extension
         'Xlib:  extension "RANDR" missing on display ":99".',

         # Related with scapy, we're not root, tcpdump is not available
         'WARNING: Failed to execute tcpdump. Check it is installed and in'
         ' the PATH',

         # Warnings/log messages related with phply
         'Generating LALR tables',
         'WARNING: 2 shift/reduce conflicts',

         # Googled: only a warning related with the CV library
         'libdc1394 error: Failed to initialize libdc1394',

         # Strange error with gtk3 vs gtk2?
         '/home/ubuntu/virtualenvs/venv-2.7.3/local/lib/python2.7/site-'
         'packages/logilab/astng/raw_building.py:167: Warning: Attempt '
         'to add property GtkSettings::gtk-label-select-on-focus after '
         'class was initialised',

         '/home/ubuntu/virtualenvs/venv-2.7.3/local/lib/python2.7/site-'
         'packages/logilab/astng/raw_building.py:167: Warning: Attempt '
         'to add property GtkSettings::gtk-menu-popup-delay after class'
         ' was initialised',

         # Same as above
         '  basenames, member.__doc__)']
