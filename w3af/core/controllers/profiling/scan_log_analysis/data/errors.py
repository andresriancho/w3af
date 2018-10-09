import re

ERRORS_RE = [re.compile('Unhandled exception "(.*?)"'),
             re.compile('traceback', re.IGNORECASE),
             re.compile('w3af-crash'),
             re.compile('scan was able to continue by ignoring those'),
             re.compile('The scan will stop')]


def show_errors(scan):
    scan.seek(0)

    errors = []

    for line in scan:
        for error_re in ERRORS_RE:
            match = error_re.search(line)
            if match:
                errors.append(line)

    if not errors:
        print('The scan finished without errors / exceptions.')
        return

    print('The scan generated %s errors during the run.' % len(errors))

    print('The following errors / exceptions were identified:')
    for error in errors:
        print('    - %s' % error)
