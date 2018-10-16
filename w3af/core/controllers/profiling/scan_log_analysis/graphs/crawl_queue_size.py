import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

CRAWLINFRA_DISK_DICT = re.compile('The current CrawlInfraIn DiskDict size is (\d*).')


def get_queue_size_crawl_data(scan_log_filename, scan):
    scan.seek(0)

    crawl_queue_sizes = []
    crawl_queue_timestamps = []

    for line in scan:
        match = CRAWLINFRA_DISK_DICT.search(line)
        if match:
            crawl_queue_sizes.append(int(match.group(1)))
            crawl_queue_timestamps.append(get_line_epoch(line))

    return crawl_queue_sizes, crawl_queue_timestamps


def draw_queue_size_crawl(scan_log_filename, scan):
    crawl_queue_sizes, crawl_queue_timestamps = get_queue_size_crawl_data(scan_log_filename, scan)

    # Get the last timestamp to use as max in the graphs
    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    crawl_queue_timestamps = [ts - first_timestamp for ts in crawl_queue_timestamps]

    if not crawl_queue_sizes:
        print('No crawl consumer queue size data found')
        return

    print('Crawl consumer queue size')
    print('    Latest queue size value: %s' % crawl_queue_sizes[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Items in CrawlInfra queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(crawl_queue_timestamps,
             crawl_queue_sizes,
             label='Crawl')

    print(fig.show())
    print('')
