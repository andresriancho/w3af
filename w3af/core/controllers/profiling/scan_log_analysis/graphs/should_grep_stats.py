import re
import json
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)


SHOULD_GREP_STATS = re.compile("Grep consumer should_grep\\(\\) stats: (.*)$")

def to_dict(match_data):
    match_data = match_data.replace("'", '"')
    return json.loads(match_data)


def get_should_grep_data(scan_log_filename, scan):
    scan.seek(0)

    should_grep_data = []
    should_grep_timestamps = []

    for line in scan:
        match = SHOULD_GREP_STATS.search(line)
        if not match:
            continue

        try:
            stats_dict = to_dict(match.group(1))
        except:
            print('Warning: %s is not valid JSON' % match.group(1))
            continue
        else:
            should_grep_data.append(stats_dict)
            should_grep_timestamps.append(get_line_epoch(line))

    return should_grep_data, should_grep_timestamps


def draw_should_grep(scan_log_filename, scan):
    should_grep_data, should_grep_timestamps = get_should_grep_data(scan_log_filename, scan)

    # Get the last timestamp to use as max in the graphs
    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    should_grep_timestamps = [ts - first_timestamp for ts in should_grep_timestamps]

    if not should_grep_data:
        print('No should_grep data found')
        return

    last_data = should_grep_data[-1]

    print('should_grep() stats')
    print('    Latest should_grep() count: %r' % last_data)

    # Calculate %
    last_data = should_grep_data[-1]
    total = sum(v for k, v in last_data.iteritems())
    total = float(total)
    data_percent = dict((k, round((v / total) * 100)) for k, v in last_data.iteritems())
    print('    Latest should_grep() percentages: %r' % data_percent)
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Percentage of rejected and accepted HTTP request and response grep tasks'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    for key in should_grep_data[-1].keys():
        key_slice = []

        for data_point in should_grep_data:
            total = sum(v for k, v in data_point.iteritems())
            total = float(total)
            if total == 0:
                key_slice.append(0)
                continue

            data_percent = dict((k, (v / total) * 100) for k, v in data_point.iteritems())
            key_slice.append(data_percent[key])

        fig.plot(should_grep_timestamps,
                 key_slice,
                 label=key)

    print(fig.show(legend=True))
    print('')
