from utils.output import KeyValueOutput


NOT_FOUND_RESPONSE = ('Received response for 404 URL',)


def get_not_found_requests(scan_log_filename, scan):
    scan.seek(0)
    not_found_count = 0

    for line in scan:
        for error in NOT_FOUND_RESPONSE:
            if error in line:
                not_found_count += 1

    return KeyValueOutput('not_found_requests',
                          '404 requests sent by is_404()',
                          not_found_count)
