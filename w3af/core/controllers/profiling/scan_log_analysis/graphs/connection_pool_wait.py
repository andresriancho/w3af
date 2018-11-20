import re
import plotille

from utils.graph import num_formatter
from utils.output import KeyValueOutput
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

CONNECTION_POOL_WAIT = re.compile('Waited (.*?)s for a connection to be available in the pool.')


def get_connection_pool_wait_data(scan_log_filename, scan):
    scan.seek(0)

    connection_pool_waits = []
    connection_pool_timestamps = []

    for line in scan:
        match = CONNECTION_POOL_WAIT.search(line)
        if match:
            connection_pool_waits.append(float(match.group(1)))
            connection_pool_timestamps.append(get_line_epoch(line))

    return connection_pool_waits, connection_pool_timestamps


def get_time_waited_by_workers(scan_log_filename, scan):
    connection_pool_waits, connection_pool_timestamps = get_connection_pool_wait_data(scan_log_filename, scan)

    return KeyValueOutput('connection_pool_wait',
                          'Time waited for worker threads for an available TCP/IP connection',
                          '%.2f seconds' % sum(connection_pool_waits))


def draw_connection_pool_wait(scan_log_filename, scan):
    connection_pool_waits, connection_pool_timestamps = get_connection_pool_wait_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    connection_pool_timestamps = [ts - first_timestamp for ts in connection_pool_timestamps]

    if not connection_pool_waits:
        print('No connection pool wait data found')
        return

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Waited time'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(connection_pool_timestamps,
             connection_pool_waits)

    print(fig.show())
    print('')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Count'
    fig.x_label = 'Time waiting for available TCP/IP connection'
    fig.set_x_limits(min_=0)
    fig.set_y_limits(min_=0)
    fig.color_mode = 'byte'

    if len(connection_pool_waits) <= 2:
        print('Not enough connection pool wait data to create histogram')
        return

    print('Time waiting for available TCP/IP connection')
    print('')
    print(plotille.hist(connection_pool_waits, bins=25))
    print('')
    print('')
