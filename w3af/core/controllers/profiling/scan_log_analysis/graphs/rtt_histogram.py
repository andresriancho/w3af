import re
import plotille

from utils.graph import num_formatter


RTT_RE = re.compile('\(.*?rtt=(.*?),.*\)')


def get_rtt_histogram_data(scan_log_filename, scan):
    scan.seek(0)
    rtts = []

    for line in scan:
        match = RTT_RE.search(line)
        if match:
            rtts.append(float(match.group(1)))

    return rtts


def draw_rtt_histogram(scan_log_filename, scan):
    rtts = get_rtt_histogram_data(scan_log_filename, scan)

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Count'
    fig.x_label = 'RTT'
    fig.set_x_limits(min_=0)
    fig.set_y_limits(min_=0)
    fig.color_mode = 'byte'

    print('[rtt_histogram]')
    print('')
    print(plotille.hist(rtts, bins=25))
    print('')
