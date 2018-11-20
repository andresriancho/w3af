import re
import plotille

from utils.graph import num_formatter
from utils.utils import get_line_epoch, InvalidTimeStamp

HTTP_CODE_RE = re.compile('returned HTTP code "(.*?)"')


def get_http_requests_over_time_data(scan_log_filename, scan):
    scan.seek(0)
    requests_by_minute = []
    requests_in_this_minute = 0

    line = scan.readline()
    prev_line_epoch = get_line_epoch(line)

    for line in scan:

        match = HTTP_CODE_RE.search(line)
        if match:
            requests_in_this_minute += 1

        try:
            cur_line_epoch = get_line_epoch(line)
        except InvalidTimeStamp:
            continue

        if cur_line_epoch - prev_line_epoch > 60:
            prev_line_epoch = cur_line_epoch
            requests_by_minute.append(requests_in_this_minute)
            requests_in_this_minute = 0

    return requests_by_minute


def draw_http_requests_over_time(scan_log_filename, scan):
    requests_by_minute = get_http_requests_over_time_data(scan_log_filename, scan)

    print('HTTP requests sent by minute')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'HTTP requests'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=None)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(xrange(len(requests_by_minute)),
             requests_by_minute)

    print(fig.show())
    print('')
