HTTP_ERRORS = ('Failed to HTTP',
               'Raising HTTP error')


def show_http_errors(scan):
    scan.seek(0)
    error_count = 0

    for line in scan:
        for error in HTTP_ERRORS:
            if error in line:
                error_count += 1

    print('The scan generated %s HTTP errors' % error_count)
