import re

from utils.output import KeyValueOutput
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         epoch_to_string)

SCAN_FINISHED_IN = re.compile('Scan finished in (.*).')


def get_scan_finished_in(scan_log_filename, scan):
    scan.seek(0)

    first_timestamp = get_first_timestamp(scan)

    for line in scan:
        match = SCAN_FINISHED_IN.search(line)
        if match:
            return KeyValueOutput('scan_time',
                                  'Scan time and state',
                                  {'finished': True,
                                   'scan_time': match.group(1)})

    last_timestamp = get_last_timestamp(scan)

    scan_run_time = last_timestamp - first_timestamp

    return KeyValueOutput('scan_time',
                          'Scan time and state',
                          {'finished': False,
                           'scan_time': epoch_to_string(scan_run_time)})
