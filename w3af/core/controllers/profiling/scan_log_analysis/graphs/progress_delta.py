import re
import plotille

from utils.graph import num_formatter
from utils.utils import (get_first_timestamp,
                         get_last_timestamp,
                         get_line_epoch)

SCAN_FINISHED_IN = re.compile('Scan finished in (.*).')
JOIN_TIMES = re.compile('(.*?) took (.*?) seconds to join\(\)')
SCAN_PROGRESS = re.compile('The scan will finish in .*? seconds \((.*?)% done\)')
CALCULATED_ETA = re.compile('Calculated (.*?) ETA: (.*?) seconds')
CRAWL_INFRA_FINISHED = 'Producer CrawlInfra has finished'


def show_progress_delta(scan_log_filename, scan):
    first_timestamp = get_first_timestamp(scan)

    #
    # Find the end times for crawl, audit, grep
    #
    scan.seek(0)

    crawl_end_timestamp = None
    audit_end_timestamp = None
    grep_end_timestamp = None

    for line in scan:
        if CRAWL_INFRA_FINISHED in line:
            crawl_end_timestamp = get_line_epoch(line)

        if 'seconds to join' not in line:
            continue

        match = JOIN_TIMES.search(line)
        if match:
            if 'audit' in line.lower():
                audit_end_timestamp = get_line_epoch(line)
            if 'grep' in line.lower():
                grep_end_timestamp = get_line_epoch(line)

    #
    # Find the crawl, audit and grep progress estimations
    #
    scan.seek(0)

    crawl_progress = []
    crawl_progress_timestamps = []

    audit_progress = []
    audit_progress_timestamps = []

    grep_progress = []
    grep_progress_timestamps = []

    for line in scan:
        match = CALCULATED_ETA.search(line)
        if match:
            ts = get_line_epoch(line)

            eta = match.group(2)
            if eta == 'None':
                eta = '0.0'

            eta = float(eta)
            percentage = (ts - first_timestamp) / (ts - first_timestamp + eta) * 100

            if 'crawl' in line.lower():
                crawl_progress_timestamps.append(ts)
                crawl_progress.append(percentage)

            if 'audit' in line.lower():
                audit_progress_timestamps.append(ts)
                audit_progress.append(percentage)

            if 'grep' in line.lower():
                grep_progress_timestamps.append(ts)
                grep_progress.append(percentage)

    # Make the timestamps relative to the scan finish
    crawl_progress_timestamps = [ts - first_timestamp for ts in crawl_progress_timestamps]
    audit_progress_timestamps = [ts - first_timestamp for ts in audit_progress_timestamps]
    grep_progress_timestamps = [ts - first_timestamp for ts in grep_progress_timestamps]

    #
    # Find the overall progress estimations
    #
    scan.seek(0)

    progress = []
    progress_timestamps = []

    for line in scan:
        match = SCAN_PROGRESS.search(line)
        if match:
            progress.append(int(match.group(1)))
            progress_timestamps.append(get_line_epoch(line))

    # Get the last timestamp to use as max in the graphs
    progress_timestamps = [ts - first_timestamp for ts in progress_timestamps]

    scan.seek(0)

    first_timestamp = get_first_timestamp(scan)
    finished_timestamp = None

    for line in scan:
        match = SCAN_FINISHED_IN.search(line)
        if match:
            finished_timestamp = get_line_epoch(line)

    finished_timestamp = finished_timestamp or get_last_timestamp(scan)
    spent_time_epoch = finished_timestamp - first_timestamp

    print('Progress delta (estimated vs. real)')
    print('')

    if crawl_progress and crawl_end_timestamp is not None:
        fig = plotille.Figure()
        fig.width = 90
        fig.height = 20
        fig.register_label_formatter(float, num_formatter)
        fig.register_label_formatter(int, num_formatter)
        fig.y_label = 'Progress'
        fig.x_label = 'Time'
        fig.color_mode = 'byte'
        fig.set_x_limits(min_=0, max_=spent_time_epoch)
        fig.set_y_limits(min_=0, max_=None)

        fig.plot(crawl_progress_timestamps,
                 crawl_progress,
                 label='Crawl (estimated)')

        crawl_real_spent = int(crawl_end_timestamp) - int(first_timestamp)
        crawl_real_progress_timestamps = range(int(first_timestamp),
                                               int(crawl_end_timestamp),
                                               1)
        crawl_real_progress_timestamps = [ts - first_timestamp for ts in crawl_real_progress_timestamps]

        crawl_real_progress = []

        for ts in crawl_real_progress_timestamps:
            crawl_real_progress.append(float(ts) / crawl_real_spent * 100)

        fig.plot(crawl_real_progress_timestamps,
                 crawl_real_progress,
                 label='Crawl (real)')

        print(fig.show(legend=True))
        print('')
        print('')

    if audit_progress and audit_end_timestamp is not None:
        fig = plotille.Figure()
        fig.width = 90
        fig.height = 20
        fig.register_label_formatter(float, num_formatter)
        fig.register_label_formatter(int, num_formatter)
        fig.y_label = 'Progress'
        fig.x_label = 'Time'
        fig.color_mode = 'byte'
        fig.set_x_limits(min_=0, max_=spent_time_epoch)
        fig.set_y_limits(min_=0, max_=None)

        fig.plot(audit_progress_timestamps,
                 audit_progress,
                 label='Audit (estimated)')

        audit_real_spent = int(audit_end_timestamp) - int(first_timestamp)
        audit_real_progress_timestamps = range(int(first_timestamp),
                                               int(audit_end_timestamp),
                                               1)
        audit_real_progress_timestamps = [ts - first_timestamp for ts in audit_real_progress_timestamps]

        audit_real_progress = []

        for ts in audit_real_progress_timestamps:
            audit_real_progress.append(float(ts) / audit_real_spent * 100)

        fig.plot(audit_real_progress_timestamps,
                 audit_real_progress,
                 label='Audit (real)')

        print(fig.show(legend=True))
        print('')
        print('')

    if grep_progress and grep_end_timestamp is not None:
        fig = plotille.Figure()
        fig.width = 90
        fig.height = 20
        fig.register_label_formatter(float, num_formatter)
        fig.register_label_formatter(int, num_formatter)
        fig.y_label = 'Progress'
        fig.x_label = 'Time'
        fig.color_mode = 'byte'
        fig.set_x_limits(min_=0, max_=spent_time_epoch)
        fig.set_y_limits(min_=0, max_=None)

        fig.plot(grep_progress_timestamps,
                 grep_progress,
                 label='Grep (estimated)')

        grep_real_spent = int(grep_end_timestamp) - int(first_timestamp)
        grep_real_progress_timestamps = range(int(first_timestamp),
                                              int(grep_end_timestamp),
                                              1)
        grep_real_progress_timestamps = [ts - first_timestamp for ts in grep_real_progress_timestamps]

        grep_real_progress = []

        for ts in grep_real_progress_timestamps:
            grep_real_progress.append(float(ts) / grep_real_spent * 100)

        fig.plot(grep_real_progress_timestamps,
                 grep_real_progress,
                 label='Grep (real)')

        print(fig.show(legend=True))
        print('')
        print('')

    if not progress:
        print('No progress data to calculate deltas (requirement: enable xml_file plugin)')
        return

    if finished_timestamp is None:
        print('The scan did not finish. Can not show progress delta.')
        return

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, num_formatter)
    fig.register_label_formatter(int, num_formatter)
    fig.y_label = 'Progress'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(progress_timestamps,
             progress,
             label='Overall (estimated)')

    real_progress = []
    for ts in progress_timestamps:
        real_progress_i = ts / float(spent_time_epoch) * 100
        real_progress.append(real_progress_i)

    fig.plot(progress_timestamps,
             real_progress,
             label='Overall (real)')

    print(fig.show(legend=True))
    print('')
    print('')
