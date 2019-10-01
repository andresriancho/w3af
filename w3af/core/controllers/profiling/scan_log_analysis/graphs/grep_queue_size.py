import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

GREP_DISK_DICT = re.compile('The current GrepIn DiskDict size is (\d*)\.')


def get_queue_size_grep_data(scan_log_filename, scan):
    scan.seek(0)

    grep_queue_sizes = []
    grep_queue_timestamps = []

    for line in scan:
        match = GREP_DISK_DICT.search(line)
        if match:
            grep_queue_sizes.append(int(match.group(1)))
            grep_queue_timestamps.append(get_line_epoch(line))

    return grep_queue_sizes, grep_queue_timestamps


def draw_queue_size_grep(scan_log_filename, scan):
    grep_queue_sizes, grep_queue_timestamps = get_queue_size_grep_data(scan_log_filename, scan)

    # Get the last timestamp to use as max in the graphs
    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    grep_queue_timestamps = [ts - first_timestamp for ts in grep_queue_timestamps]

    if not grep_queue_sizes:
        print('No grep consumer queue size data found')
        return

    print('Grep consumer queue size')
    print('    Latest queue size value: %s' % grep_queue_sizes[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Items in Grep queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(grep_queue_timestamps,
             grep_queue_sizes,
             label='Grep')

    print(fig.show())
    print('')
