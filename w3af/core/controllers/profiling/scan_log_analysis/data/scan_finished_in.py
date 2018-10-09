import re

from utils.utils import (get_first_timestamp,
                                                                           get_last_timestamp,
                                                                           epoch_to_string)

SCAN_FINISHED_IN = re.compile('Scan finished in (.*).')


def show_scan_finished_in(scan_log_filename, scan):
    scan.seek(0)

    first_timestamp = get_first_timestamp(scan)

    for line in scan:
        match = SCAN_FINISHED_IN.search(line)
        if match:
            print(match.group(0))
            return

    last_timestamp = get_last_timestamp(scan)

    scan_run_time = last_timestamp - first_timestamp
    print('Scan is still running!')
    print('    Started %s ago' % epoch_to_string(scan_run_time))
