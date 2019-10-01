import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

ACTIVE_THREADS = re.compile('The framework has (.*?) active threads.')


def get_active_threads_data(scan_log_filename, scan):
    scan.seek(0)

    active_threads = []
    active_threads_timestamps = []

    for line in scan:
        match = ACTIVE_THREADS.search(line)
        if match:
            active_threads.append(float(match.group(1)))
            active_threads_timestamps.append(get_line_epoch(line))

    return active_threads, active_threads_timestamps


def draw_active_threads(scan_log_filename, scan):
    active_threads, active_threads_timestamps = get_active_threads_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_epoch = last_timestamp - first_timestamp
    active_threads_timestamps = [ts - first_timestamp for ts in active_threads_timestamps]

    if not active_threads:
        print('No active thread data found')
        return

    print('Active thread count over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Thread count'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(active_threads_timestamps,
             active_threads)

    print(fig.show())
    print('')
