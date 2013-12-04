#!/usr/bin/env python

import os
import sys
import tempfile

ARTIFACTS_DIR = os.environ.get('CIRCLE_ARTIFACTS', tempfile.gettempdir())
LOG_FILE = os.path.join(ARTIFACTS_DIR, 'django-moth.log')

TRACEBACK = 'Traceback (most recent call last)'


def check_traceback_in_log():
    '''
    I don't want any tracebacks in the django-moth log. Tracebacks, even
    in this vulnerable application, should be handled properly. They usually
    tell me that I forgot something.
    '''
    for line in file(LOG_FILE):
        if TRACEBACK in line:
            print('Found a traceback in django-moth.log check the build '\
                  ' artifacts at CircleCI.')
            sys.exit(1)

if __name__ == '__main__':
    check_traceback_in_log()
    