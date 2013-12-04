#!/usr/bin/env python

import os
import sys
import tempfile

ARTIFACTS_DIR = os.environ.get('CIRCLE_ARTIFACTS', tempfile.gettempdir())
LOG_NAME = 'django-moth.log'
LOG_FILE = os.path.join(ARTIFACTS_DIR, LOG_NAME)

TRACEBACK = 'Traceback (most recent call last)'


def check_traceback_in_log():
    '''
    I don't want any tracebacks in the django-moth log. Tracebacks, even
    in this vulnerable application, should be handled properly. They usually
    tell me that I forgot something.
    '''
    for line in file(LOG_FILE):
        if TRACEBACK in line:
            msg = 'Found a traceback in %s, check the build artifacts at CircleCI.'
            print(msg % LOG_NAME)
            sys.exit(1)
            
    print('No tracebacks found in %s' % LOG_NAME)

if __name__ == '__main__':
    check_traceback_in_log()
    