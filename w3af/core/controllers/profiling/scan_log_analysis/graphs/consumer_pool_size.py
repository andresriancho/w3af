import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

IDLE_CONSUMER_WORKERS = re.compile('\[.*? - .*?\] (.*?)% of (.*?) workers are idle.')


def get_consumer_pool_size_data(scan_log_filename, scan):
    scan.seek(0)

    consumer_pool_perc_audit = []
    consumer_pool_timestamps_audit = []

    consumer_pool_perc_crawl = []
    consumer_pool_timestamps_crawl = []

    worker_pool_perc = []
    worker_pool_timestamps = []

    for line in scan:
        match = IDLE_CONSUMER_WORKERS.search(line)
        if not match:
            continue

        percent = int(match.group(1))
        is_audit = 'audit' in match.group(2).lower()
        is_crawl = 'crawl' in match.group(2).lower()

        if is_audit:
            consumer_pool_perc_audit.append(percent)
            consumer_pool_timestamps_audit.append(get_line_epoch(line))
        elif is_crawl:
            consumer_pool_perc_crawl.append(percent)
            consumer_pool_timestamps_crawl.append(get_line_epoch(line))
        else:
            worker_pool_perc.append(percent)
            worker_pool_timestamps.append(get_line_epoch(line))

    return (consumer_pool_perc_audit, consumer_pool_timestamps_audit,
            consumer_pool_perc_crawl, consumer_pool_timestamps_crawl,
            worker_pool_perc, worker_pool_timestamps)


def draw_consumer_pool_size(scan_log_filename, scan):
    (consumer_pool_perc_audit, consumer_pool_timestamps_audit,
     consumer_pool_perc_crawl, consumer_pool_timestamps_crawl,
     worker_pool_perc, worker_pool_timestamps) = get_consumer_pool_size_data(scan_log_filename, scan)

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    consumer_pool_timestamps_audit = [ts - first_timestamp for ts in consumer_pool_timestamps_audit]
    consumer_pool_timestamps_crawl = [ts - first_timestamp for ts in consumer_pool_timestamps_crawl]
    worker_pool_timestamps = [ts - first_timestamp for ts in worker_pool_timestamps]

    if not consumer_pool_perc_audit and not consumer_pool_perc_crawl:
        print('No thread pool data found')
        return

    print('Idle thread pool workers over time')
    print('    Latest idle core workers %s%%' % worker_pool_perc[-1])

    if consumer_pool_perc_audit:
        print('    Latest idle audit workers %s%%' % consumer_pool_perc_audit[-1])

    if consumer_pool_perc_crawl:
        print('    Latest idle crawl-infra workers %s%%' % consumer_pool_perc_crawl[-1])

    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Idle worker (%)'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=101)

    fig.plot(consumer_pool_timestamps_audit,
             consumer_pool_perc_audit,
             label='Idle audit workers',
             lc=50)

    fig.plot(consumer_pool_timestamps_crawl,
             consumer_pool_perc_crawl,
             label='Idle crawl workers',
             lc=170)

    fig.plot(worker_pool_timestamps,
             worker_pool_perc,
             label='Idle core workers',
             lc=250)

    print(fig.show(legend=True))
    print('')
