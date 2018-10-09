import re
import plotille

from utils.graph import _num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

EXTENDED_URLLIB_ERRORS_RE = re.compile('ExtendedUrllib error rate is at (.*?)%')


def show_extended_urllib_error_rate(scan):
    error_rate = []
    error_rate_timestamps = []

    for line in scan:
        match = EXTENDED_URLLIB_ERRORS_RE.search(line)
        if match:
            error_rate.append(int(match.group(1)))
            error_rate_timestamps.append(get_line_epoch(line))

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_epoch = last_timestamp - first_timestamp
    error_rate_timestamps = [ts - first_timestamp for ts in error_rate_timestamps]

    if not error_rate:
        print('No error rate information found')
        print('')
        return

    print('Extended URL library error rate')
    print('    Error rate exceeded 10%%: %s' % (max(error_rate) > 10,))
    print('    Error rate exceeded 20%%: %s' % (max(error_rate) > 10,))
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
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
    print('')
