import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

AUDITOR_DISK_DICT = re.compile('The current AuditorIn DiskDict size is (\d*).')


def get_queue_size_audit_data(scan_log_filename, scan):
    scan.seek(0)

    auditor_queue_sizes = []
    auditor_queue_timestamps = []

    for line in scan:
        match = AUDITOR_DISK_DICT.search(line)
        if match:
            auditor_queue_sizes.append(int(match.group(1)))
            auditor_queue_timestamps.append(get_line_epoch(line))

    return auditor_queue_sizes, auditor_queue_timestamps


def draw_queue_size_audit(scan_log_filename, scan):
    auditor_queue_sizes, auditor_queue_timestamps = get_queue_size_audit_data(scan_log_filename, scan)

    # Get the last timestamp to use as max in the graphs
    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    auditor_queue_timestamps = [ts - first_timestamp for ts in auditor_queue_timestamps]

    if not auditor_queue_sizes:
        print('No audit consumer queue size data found')
        print('')
        return

    print('Audit consumer queue size')
    print('    Latest queue size value: %s' % auditor_queue_sizes[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Items in Audit queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(auditor_queue_timestamps,
             auditor_queue_sizes,
             label='Audit')

    print(fig.show())
    print('')
