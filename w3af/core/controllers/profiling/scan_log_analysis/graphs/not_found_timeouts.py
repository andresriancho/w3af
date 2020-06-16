import plotille

from utils.graph import num_formatter
from utils.output import KeyValueOutput
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

NOT_FOUND_TIMEOUT = 'is_404() took more than'


def get_not_found_timeouts_data(scan_log_filename, scan):
    scan.seek(0)

    timeout_count = 0
    timeout_errors = []
    timeout_errors_timestamps = []

    for line in scan:
        if NOT_FOUND_TIMEOUT in line:
            timeout_count += 1
            timeout_errors.append(timeout_count)
            timeout_errors_timestamps.append(get_line_epoch(line))

    return timeout_count, timeout_errors, timeout_errors_timestamps


def get_not_found_timeouts_summary(scan_log_filename, scan):
    timeout_count, _, _ = get_not_found_timeouts_data(scan_log_filename, scan)

    return KeyValueOutput('not_found_timeout_summary',
                          'is_404() timeouts',
                          {'count': timeout_count})


def draw_not_found_timeouts(scan_log_filename, scan):
    timeout_count, timeout_errors, timeout_errors_timestamps = get_not_found_timeouts_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_epoch = last_timestamp - first_timestamp
    timeout_errors_timestamps = [ts - first_timestamp for ts in timeout_errors_timestamps]

    if not timeout_errors:
        print('No is_404() timeouts found')
        print('')
        return

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Timeouts'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_epoch)
    fig.set_y_limits(min_=0, max_=timeout_count)

    fig.plot(timeout_errors_timestamps,
             timeout_errors,
             label='is_404() timeouts',
             lc=50)

    print(fig.show(legend=True))
    print('')
