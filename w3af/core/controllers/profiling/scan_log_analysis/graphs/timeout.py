import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

SOCKET_TIMEOUT = re.compile('Updating socket timeout for .* from .* to (.*?) seconds')


def get_timeout_data(scan_log_filename, scan):
    scan.seek(0)
    timeouts = []
    timeout_timestamps = []

    for line in scan:
        match = SOCKET_TIMEOUT.search(line)
        if match:
            timeouts.append(float(match.group(1)))
            timeout_timestamps.append(get_line_epoch(line))

    return timeouts, timeout_timestamps


def draw_timeout(scan_log_filename, scan):
    scan.seek(0)
    timeouts, timeout_timestamps = get_timeout_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    timeout_timestamps = [ts - first_timestamp for ts in timeout_timestamps]

    if not timeouts:
        print('No socket timeout data found')
        return

    print('Socket timeout over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Socket timeout'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(timeout_timestamps,
             timeouts,
             label='Timeout')

    print(fig.show())
    print('')
