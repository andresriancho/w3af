from w3af.core.controllers.output_manager import out
from w3af.core.controllers.tests.running_tests import is_running_tests

DEBUG = is_running_tests() or False


def to_utf8_raw(unicode_or_str):
    if isinstance(unicode_or_str, unicode):
        # TODO: Is 'ignore' the best option here?
        return unicode_or_str.encode('utf-8', 'ignore')
    return unicode_or_str


def debug(msg):
    if DEBUG:
        out.debug(msg)

        if is_running_tests():
            print(msg)


def error(msg):
    if DEBUG:
        out.error(msg)

        if is_running_tests():
            print(msg)
