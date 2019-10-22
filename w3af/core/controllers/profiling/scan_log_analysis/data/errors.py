import re

from utils.output import KeyValueOutput


ERRORS_RE = [re.compile('Unhandled exception "(.*?)"'),
             re.compile('traceback', re.IGNORECASE),
             re.compile('w3af-crash'),
             re.compile('scan was able to continue by ignoring those'),
             re.compile('The scan will stop')]

IGNORES = [u'The fuzzable request router loop will break']


# Original log line without any issues:
#
#     AuditorWorker worker pool internal thread state: (worker: True, task: True, result: True)
#
# When there is ONE missing True, we have issues, when the pool finishes all three are False
POOL_INTERNAL = 'pool internal thread state'


def matches_ignore(line):
    for ignore in IGNORES:
        if ignore in line:
            return True

    return False


def get_errors(scan_log_filename, scan):
    scan.seek(0)

    errors = []

    for line in scan:
        for error_re in ERRORS_RE:
            match = error_re.search(line)
            if match and not matches_ignore(line):
                line = line.strip()
                errors.append(line)

    scan.seek(0)

    for line in scan:
        if POOL_INTERNAL not in line:
            continue

        if line.count('True') in (0, 3):
            continue

        line = line.strip()
        errors.append(line)

    output = KeyValueOutput('errors', 'errors and exceptions', {'count': len(errors),
                                                                'errors': errors})

    return output
