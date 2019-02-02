import re
import plotille

from utils.graph import num_formatter
from utils.utils import get_first_timestamp, get_last_timestamp, get_line_epoch


RTT_RE = re.compile('\(.*?rtt=(.*?),.*\)')


def get_rtt_data(scan_log_filename, scan):
    scan.seek(0)
    rtt = []
    rtt_timestamps = []

    for line in scan:
        match = RTT_RE.search(line)
        if match:
            rtt.append(float(match.group(1)))
            rtt_timestamps.append(get_line_epoch(line))

    return rtt, rtt_timestamps


def draw_rtt(scan_log_filename, scan):
    scan.seek(0)
    rtt, rtt_timestamps = get_rtt_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    rtt_timestamps = [ts - first_timestamp for ts in rtt_timestamps]

    if not rtt:
        print('No RTT data found')
        return

    print('RTT over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'RTT'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(rtt_timestamps,
             rtt,
             label='RTT')

    print(fig.show())
    print('')
