from utils.utils import get_line_epoch, InvalidTimeStamp
from utils.output import KeyValueOutput


def get_freeze_locations(scan_log_filename, scan):
    """
    [Wed Nov  1 23:43:16 2017 - debug] ...
    [Wed Nov  1 23:43:19 2017 - debug] ...

    3 seconds without writing anything to the log? That is a freeze!

    :param scan: The file handler for the scan log
    :return: None, all printed to the output
    """
    scan.seek(0)
    freezes = []

    previous_line_time = get_line_epoch(scan.readline())

    for line in scan:
        try:
            current_line_epoch = get_line_epoch(line)
        except InvalidTimeStamp:
            continue

        time_spent = current_line_epoch - previous_line_time

        if time_spent > 5:
            line = line.strip()
            freezes.append(line)

        previous_line_time = current_line_epoch

    return KeyValueOutput('debug_log_freeze',
                          'Delays greater than 5 seconds between two log lines',
                          freezes)
