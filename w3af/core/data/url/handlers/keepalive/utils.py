import os

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.tests.running_tests import is_running_tests


DEBUG = os.environ.get('DEBUG', '0') == '1'


def to_utf8_raw(unicode_or_str):
    if isinstance(unicode_or_str, unicode):
        # TODO: Is 'ignore' the best option here?
        return unicode_or_str.encode('utf-8', 'ignore')
    return unicode_or_str


def debug(msg):
    if DEBUG:
        msg = '[keepalive] %s' % msg
        om.out.debug(msg)

        if is_running_tests():
            # print(msg)
            pass


def error(msg):
    if DEBUG:
        msg = '[keepalive] %s' % msg
        om.out.error(msg)

        if is_running_tests():
            # print(msg)
            pass
