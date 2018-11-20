from utils.output import KeyValueOutput


HTTP_ERRORS = ('Failed to HTTP',
               'Raising HTTP error')


def get_http_errors(scan_log_filename, scan):
    scan.seek(0)
    error_count = 0

    for line in scan:
        for error in HTTP_ERRORS:
            if error in line:
                error_count += 1

    return KeyValueOutput('http_errors',
                          'HTTP errors',
                          error_count)
