#!/usr/bin/env python

import os
import sys
import tempfile

ARTIFACTS_DIR = os.environ.get('CIRCLE_ARTIFACTS', tempfile.gettempdir())

HTTP_LOG = 'django-moth.log'
SSL_LOG = 'django-moth-ssl.log'

TRACEBACK = 'Traceback (most recent call last)'


def check_traceback_in_log():
    """
    I don't want any tracebacks in the django-moth log. Tracebacks, even
    in this vulnerable application, should be handled properly. They usually
    tell me that I forgot something.
    """
    for log_file in (HTTP_LOG, SSL_LOG):
        
        log_path = os.path.join(ARTIFACTS_DIR, log_file)
        
        for line in file(log_path):
            if TRACEBACK in line:
                msg = 'Found a traceback in %s, check the build artifacts'\
                      ' at CircleCI.'
                print(msg % log_file)
                sys.exit(1)
            
    print('No tracebacks found in django moth logs.')

if __name__ == '__main__':
    check_traceback_in_log()
    