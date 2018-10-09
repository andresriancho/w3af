from utils.utils import get_line_epoch, InvalidTimeStamp


def show_freeze_locations(scan_log_filename, scan):
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

            if len(line) >= 80:
                msg = 'Found %s second freeze at: %s...' % (time_spent, line[:80])
            else:
                msg = 'Found %s second freeze at: %s' % (time_spent, line)

            freezes.append(msg)

        previous_line_time = current_line_epoch

    if not freezes:
        print('No delays greater than 3 seconds were found between two scan log lines')
        return

    print('Found the delays greater than 3 seconds around these scan log lines:')
    for freeze in freezes:
        print('    - %s' % freeze)
