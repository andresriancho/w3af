import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)


CACHE_RATE = re.compile('The 404 cache has a (\d*).*? % hit rate')


def get_not_found_cache_rate_data(scan_log_filename, scan):
    scan.seek(0)

    cache_rate = []
    cache_rate_timestamps = []

    for line in scan:
        match = CACHE_RATE.search(line)
        if match:
            cache_rate.append(int(match.group(1)))
            cache_rate_timestamps.append(get_line_epoch(line))

    return cache_rate, cache_rate_timestamps


def draw_not_found_cache_rate_over_time(scan_log_filename, scan):
    cache_rate, cache_rate_timestamps = get_not_found_cache_rate_data(scan_log_filename, scan)

    # Get the last timestamp to use as max in the graphs
    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    grep_queue_timestamps = [ts - first_timestamp for ts in cache_rate_timestamps]

    if not cache_rate:
        print('No 404 cache rate data found')
        return

    print('404 cache hit rate')
    print('    Latest hit rate value: %s %%' % cache_rate[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Hit rate (%)'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(grep_queue_timestamps,
             cache_rate,
             label='Hit rate')

    print(fig.show())
    print('')
