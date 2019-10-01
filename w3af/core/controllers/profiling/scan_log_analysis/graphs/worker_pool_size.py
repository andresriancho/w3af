import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

WORKER_POOL_SIZE = re.compile('the worker pool size to (.*?) ')


def get_worker_pool_size_data(scan_log_filename, scan):
    scan.seek(0)

    worker_pool_sizes = []
    worker_pool_timestamps = []

    for line in scan:
        match = WORKER_POOL_SIZE.search(line)
        if match:
            worker_pool_sizes.append(int(match.group(1)))
            worker_pool_timestamps.append(get_line_epoch(line))

    return worker_pool_sizes, worker_pool_timestamps


def draw_worker_pool_size(scan_log_filename, scan):
    worker_pool_sizes, worker_pool_timestamps = get_worker_pool_size_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    worker_pool_timestamps = [ts - first_timestamp for ts in worker_pool_timestamps]

    if not worker_pool_sizes:
        print('No worker pool size data found')
        return

    print('Worker pool size over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Worker pool size'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(worker_pool_timestamps,
             worker_pool_sizes,
             label='Workers')

    print(fig.show())
    print('')
