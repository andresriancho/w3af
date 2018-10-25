import re

from utils.output import KeyValueOutput


ERRORS_RE = [re.compile('Unhandled exception "(.*?)"'),
             re.compile('traceback', re.IGNORECASE),
             re.compile('w3af-crash'),
             re.compile('scan was able to continue by ignoring those'),
             re.compile('The scan will stop')]


def get_errors(scan_log_filename, scan):
    scan.seek(0)

    errors = []

    for line in scan:
        for error_re in ERRORS_RE:
            match = error_re.search(line)
            if match:
                line = line.strip()
                errors.append(line)

    output = KeyValueOutput('errors', 'errors and exceptions', {'count': len(errors),
                                                                'errors': errors})

    return output
