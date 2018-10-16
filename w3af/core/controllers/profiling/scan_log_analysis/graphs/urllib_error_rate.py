import re
import plotille

from utils.graph import num_formatter
from utils.output import KeyValueOutput
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

EXTENDED_URLLIB_ERRORS_RE = re.compile('ExtendedUrllib error rate is at (.*?)%')


def get_error_rate_data(scan_log_filename, scan):
    error_rate = []
    error_rate_timestamps = []

    for line in scan:
        match = EXTENDED_URLLIB_ERRORS_RE.search(line)
        if match:
            error_rate.append(int(match.group(1)))
            error_rate_timestamps.append(get_line_epoch(line))

    return error_rate, error_rate_timestamps


def get_error_rate_summary(scan_log_filename, scan):
    error_rate, _ = get_error_rate_data(scan_log_filename, scan)

    return KeyValueOutput('error_rate_summary',
                          'Error rate summary',
                          {'Error rate exceeded 10%': False if not error_rate else max(error_rate) > 10,
                           'Error rate exceeded 20%': False if not error_rate else max(error_rate) > 20})


def draw_extended_urllib_error_rate(scan_log_filename, scan):
    error_rate, error_rate_timestamps = get_error_rate_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_epoch = last_timestamp - first_timestamp
    error_rate_timestamps = [ts - first_timestamp for ts in error_rate_timestamps]

    if not error_rate:
        print('No error rate information found')
        print('')
        return

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Error rate'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_epoch)
    fig.set_y_limits(min_=0, max_=max(error_rate) * 1.1)

    fig.plot(error_rate_timestamps,
             error_rate,
             label='Error rate')

    print(fig.show())
    print('')
