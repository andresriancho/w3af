import re
import plotille

from utils.graph import _num_formatter


RTT_RE = re.compile('\(.*?rtt=(.*?),.*\)')


def show_rtt_histo(scan_log_filename, scan):
    scan.seek(0)
    rtts = []

    for line in scan:
        match = RTT_RE.search(line)
        if match:
            rtts.append(float(match.group(1)))

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Count'
    fig.x_label = 'RTT'
    fig.set_x_limits(min_=0)
    fig.set_y_limits(min_=0)
    fig.color_mode = 'byte'

    print('RTT Histogram')
    print('')
    print(plotille.hist(rtts, bins=25))
    print('')
    print('')
