#!/usr/bin/env python

import os
import re
import sys
import time
import argparse
import datetime

from urlparse import urlparse

try:
    import plotille
except ImportError:
    print('Missing dependency, please run:\n    pip install plotille')
    sys.exit(1)

HELP = '''\
Usage: ./scan_log_analysis.py <scan.log>

This is a command line tool that helps identify differences in two scans.

The tool takes a scan log as input, and outputs:
 * Total scan time
 * Total time spent on grep, audit, crawl and output plugins for each scan
 * Total HTTP requests
 * Locations in the scan logs where the output was silent (no lines written in more than N seconds)

The scan log needs to have debug enabled in order for this tool to work as expected.

It is also possible to just watch one graph in the console using:

    --watch <function-name>

Where <function-name> is the name of the function in the scan_log_analysis.py file
you want to watch.
'''
SCAN_FINISHED_IN = re.compile('Scan finished in (.*).')

SCAN_TOOK_RE = re.compile('took (\d*\.\d\d)s to run')

HTTP_CODE_RE = re.compile('returned HTTP code "(.*?)"')
FROM_CACHE = 'from_cache=1'

SOCKET_TIMEOUT = re.compile('Updating socket timeout for .* from .* to (.*?) seconds')

EXTENDED_URLLIB_ERRORS_RE = re.compile('ExtendedUrllib error rate is at (.*?)%')

GREP_DISK_DICT = re.compile('The current GrepIn DiskDict size is (\d*).')
AUDITOR_DISK_DICT = re.compile('The current AuditorIn DiskDict size is (\d*).')
CRAWLINFRA_DISK_DICT = re.compile('The current CrawlInfraIn DiskDict size is (\d*).')

RTT_RE = re.compile('\(.*?rtt=(.*?),.*\)')

ERRORS_RE = [re.compile('Unhandled exception "(.*?)"'),
             re.compile('traceback', re.IGNORECASE),
             re.compile('w3af-crash'),
             re.compile('scan was able to continue by ignoring those'),
             re.compile('The scan will stop')]

HTTP_ERRORS = ('Failed to HTTP',
               'Raising HTTP error')

WORKER_POOL_SIZE = re.compile('the worker pool size to (.*?) ')
ACTIVE_THREADS = re.compile('The framework has (.*?) active threads.')

JOIN_TIMES = re.compile('(.*?) took (.*?) seconds to join\(\)')

CONNECTION_POOL_WAIT = re.compile('Waited (.*?)s for a connection to be available in the pool.')

WEBSPIDER_FOUND_LINK = re.compile('\[web_spider\] Found new link "(.*?)" at "(.*?)"')
IDLE_CONSUMER_WORKERS = re.compile('\[.*? - .*?\] (.*?)% of (.*?) workers are idle.')

PARSER_TIMEOUT = '[timeout] The parser took more than'
PARSER_MEMORY_LIMIT = 'The parser exceeded the memory usage limit of'
PARSER_PROCESS_MEMORY_LIMIT = re.compile('Using RLIMIT_AS memory usage limit (.*?) MB for new pool process')

GREP_PLUGIN_RE = re.compile('\] (.*?).grep\(uri=".*"\) took (.*?)s to run')


def _num_formatter(val, chars, delta, left=False):
    align = '<' if left else ''
    return '{:{}{}d}'.format(int(val), align, chars)


def epoch_to_string(spent_time):
    time_delta = datetime.timedelta(seconds=spent_time)

    weeks, days = divmod(time_delta.days, 7)

    minutes, seconds = divmod(time_delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)

    msg = ''

    if weeks == days == hours == minutes == seconds == 0:
        msg += '0 seconds'
    else:
        if weeks:
            msg += str(weeks) + ' week%s ' % ('s' if weeks > 1 else '')
        if days:
            msg += str(days) + ' day%s ' % ('s' if days > 1 else '')
        if hours:
            msg += str(hours) + ' hour%s ' % ('s' if hours > 1 else '')
        if minutes:
            msg += str(minutes) + ' minute%s ' % ('s' if minutes > 1 else '')
        if seconds:
            msg += str(seconds) + ' second%s' % ('s' if seconds > 1 else '')

    return msg


def show_scan_stats(scan):
    show_scan_finished_in(scan)

    print('')

    show_errors(scan)

    print('')

    print('Wall time used by threads:')
    show_discovery_time(scan)
    show_audit_time(scan)
    show_grep_time(scan)
    show_output_time(scan)

    print('')

    show_http_errors(scan)
    show_total_http_requests(scan)
    show_rtt_histo(scan)
    show_timeout(scan)
    show_extended_urllib_error_rate(scan)
    show_connection_pool_wait(scan)
    show_http_requests_over_time(scan)

    print('')

    show_crawling_stats(scan)
    generate_crawl_graph(scan)

    print('')

    show_queue_size_grep(scan)
    show_queue_size_audit(scan)
    show_queue_size_crawl(scan)

    print('')

    show_grep_plugin_performance(scan)

    print('')

    show_parser_errors(scan)
    show_parser_process_memory_limit(scan)

    print('')

    show_worker_pool_size(scan)
    show_active_threads(scan)
    show_consumer_pool_size(scan)

    print('')

    show_consumer_join_times(scan)

    print('')

    show_freeze_locations(scan)

    print('')

    show_known_problems(scan)


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


def get_path(url):
    return urlparse(url).path


def generate_crawl_graph(scan):
    scan.seek(0)

    data = {}

    for line in scan:
        match = WEBSPIDER_FOUND_LINK.search(line)
        if not match:
            continue
        new_link = get_path(match.group(1))
        referer = get_path(match.group(2))
        if referer in data:
            data[referer].append(new_link)
        else:
            data[referer] = [new_link]

    if not data:
        print('No web_spider data found!')

    def sort_by_len(a, b):
        return cmp(len(a), len(b))

    referers = data.keys()
    referers.sort(sort_by_len)

    print('web_spider crawling data (source -> new link)')

    previous_referer = None

    for referer in referers:
        new_links = data[referer]
        new_links.sort(sort_by_len)
        for new_link in new_links:
            if referer is previous_referer:
                spaces = ' ' * len('%s -> ' % previous_referer)
                print('%s%s' % (spaces, new_link))
            else:
                print('%s -> %s' % (referer, new_link))
                previous_referer = referer


def show_parser_process_memory_limit(scan):
    scan.seek(0)

    memory_limit = []
    memory_limit_timestamps = []

    for line in scan:
        match = PARSER_PROCESS_MEMORY_LIMIT.search(line)
        if match:
            memory_limit.append(int(match.group(1)))
            memory_limit_timestamps.append(get_line_epoch(line))

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_epoch = last_timestamp - first_timestamp
    memory_limit_timestamps = [ts - first_timestamp for ts in memory_limit_timestamps]

    if not memory_limit:
        print('No parser process memory limit information found')
        return

    print('Parser process memory limit')
    print('    Latest memory limit: %s MB' % memory_limit[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Parser memory limit (MB)'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_epoch)
    fig.set_y_limits(min_=0, max_=max(memory_limit) * 1.1)

    fig.plot(memory_limit_timestamps,
             memory_limit,
             label='Memory limit')

    print(fig.show())
    print('')
    print('')


def show_parser_errors(scan):
    scan.seek(0)

    timeout_count = 0
    timeout_errors = []
    timeout_errors_timestamps = []

    memory_count = 0
    memory_errors = []
    memory_errors_timestamps = []

    for line in scan:
        if PARSER_TIMEOUT in line:
            timeout_count += 1
            timeout_errors.append(timeout_count)
            timeout_errors_timestamps.append(get_line_epoch(line))

        if PARSER_MEMORY_LIMIT in line:
            memory_count += 1
            memory_errors.append(memory_count)
            memory_errors_timestamps.append(get_line_epoch(line))

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_epoch = last_timestamp - first_timestamp
    timeout_errors_timestamps = [ts - first_timestamp for ts in timeout_errors_timestamps]
    memory_errors_timestamps = [ts - first_timestamp for ts in memory_errors_timestamps]

    if not memory_errors and not timeout_errors:
        print('No parser errors found')
        print('')
        return

    print('Parser errors')
    print('    Timeout errors: %s' % timeout_count)
    print('    Memory errors: %s' % memory_count)
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Parser errors'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    #fig.set_x_limits(min_=0, max_=spent_epoch)
    fig.set_y_limits(min_=0, max_=max(memory_count, timeout_count))

    fig.plot(timeout_errors,
             timeout_errors_timestamps,
             label='Timeout errors',
             lc=50)

    fig.plot(memory_errors,
             memory_errors_timestamps,
             label='Memory errors',
             lc=200)

    print(fig.show(legend=True))
    print('')
    print('')


def show_active_threads(scan):
    scan.seek(0)

    active_threads = []
    active_threads_timestamps = []

    for line in scan:
        match = ACTIVE_THREADS.search(line)
        if match:
            active_threads.append(float(match.group(1)))
            active_threads_timestamps.append(get_line_epoch(line))

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_epoch = last_timestamp - first_timestamp
    active_threads_timestamps = [ts - first_timestamp for ts in active_threads_timestamps]

    if not active_threads:
        print('No active thread data found')
        return

    print('Active thread count over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Thread count'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(active_threads_timestamps,
             active_threads)

    print(fig.show())
    print('')
    print('')


def show_connection_pool_wait(scan):
    scan.seek(0)

    connection_pool_waits = []
    connection_pool_timestamps = []

    for line in scan:
        match = CONNECTION_POOL_WAIT.search(line)
        if match:
            connection_pool_waits.append(float(match.group(1)))
            connection_pool_timestamps.append(get_line_epoch(line))

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    connection_pool_timestamps = [ts - first_timestamp for ts in connection_pool_timestamps]

    if not connection_pool_waits:
        print('No connection pool wait data found')
        return

    print('Time waited for worker threads for an available TCP/IP connection')
    print('    Total: %.2f sec' % sum(connection_pool_waits))
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
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
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Count'
    fig.x_label = 'Time waiting for available TCP/IP connection'
    fig.set_x_limits(min_=0)
    fig.set_y_limits(min_=0)
    fig.color_mode = 'byte'

    print('Time waiting for available TCP/IP connection')
    print('')
    print(plotille.hist(connection_pool_waits, bins=25))
    print('')
    print('')


def show_errors(scan):
    scan.seek(0)

    errors = []

    for line in scan:
        for error_re in ERRORS_RE:
            match = error_re.search(line)
            if match:
                errors.append(line)

    if not errors:
        print('The scan finished without errors / exceptions.')
        return

    print('The following errors / exceptions were identified:')
    for error in errors:
        print('    - %s' % error)


def show_consumer_join_times(scan):
    scan.seek(0)

    join_times = []

    for line in scan:
        if 'seconds to join' not in line:
            continue

        match = JOIN_TIMES.search(line)
        if match:
            join_times.append(match.group(0))

    if not join_times:
        print('The scan log has no calls to join()')
        return

    print('These consumers were join()\'ed')
    for join_time in join_times:
        print('    - %s' % join_time)


def show_consumer_pool_size(scan):
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
    print('    Latest idle audit workers %s%%' % consumer_pool_perc_audit[-1])
    print('    Latest idle crawl-infra workers %s%%' % consumer_pool_perc_crawl[-1])
    print('    Latest idle core workers %s%%' % worker_pool_perc[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
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
    print('')


def show_worker_pool_size(scan):
    scan.seek(0)

    worker_pool_sizes = []
    worker_pool_timestamps = []

    for line in scan:
        match = WORKER_POOL_SIZE.search(line)
        if match:
            worker_pool_sizes.append(int(match.group(1)))
            worker_pool_timestamps.append(get_line_epoch(line))

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    worker_pool_timestamps = [ts - first_timestamp for ts in worker_pool_timestamps]

    if not worker_pool_sizes:
        print('No worker pool size data found')
        return

    print('Worker pool size over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Worker pool size'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(worker_pool_timestamps,
             worker_pool_sizes,
             label='Workers')

    print(fig.show())
    print('')
    print('')


def show_scan_finished_in(scan):
    scan.seek(0)

    first_timestamp = get_first_timestamp(scan)

    for line in scan:
        match = SCAN_FINISHED_IN.search(line)
        if match:
            print(match.group(0))
            return

    last_timestamp = get_last_timestamp(scan)

    scan_run_time = last_timestamp - first_timestamp
    print('Scan is still running!')
    print('    Started %s ago' % epoch_to_string(scan_run_time))


def show_http_requests_over_time(scan):
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

    print('HTTP requests sent by minute')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'HTTP requests'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=None)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(xrange(len(requests_by_minute)),
             requests_by_minute)

    print(fig.show())
    print('')
    print('')


def show_timeout(scan):
    scan.seek(0)
    timeouts = []
    timeout_timestamps = []

    for line in scan:
        match = SOCKET_TIMEOUT.search(line)
        if match:
            timeouts.append(float(match.group(1)))
            timeout_timestamps.append(get_line_epoch(line))

    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    timeout_timestamps = [ts - first_timestamp for ts in timeout_timestamps]

    if not timeouts:
        print('No socket timeout data found')
        return

    print('Socket timeout over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Socket timeout'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(timeout_timestamps,
             timeouts,
             label='Timeout')

    print(fig.show())
    print('')
    print('')


def show_rtt_histo(scan):
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


def show_queue_size_crawl(scan):
    scan.seek(0)

    crawl_queue_sizes = []
    crawl_queue_timestamps = []

    for line in scan:
        match = CRAWLINFRA_DISK_DICT.search(line)
        if match:
            crawl_queue_sizes.append(int(match.group(1)))
            crawl_queue_timestamps.append(get_line_epoch(line))

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
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
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
    print('')


def show_queue_size_audit(scan):
    scan.seek(0)

    auditor_queue_sizes = []
    auditor_queue_timestamps = []

    for line in scan:
        match = AUDITOR_DISK_DICT.search(line)
        if match:
            auditor_queue_sizes.append(int(match.group(1)))
            auditor_queue_timestamps.append(get_line_epoch(line))

    # Get the last timestamp to use as max in the graphs
    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    auditor_queue_timestamps = [ts - first_timestamp for ts in auditor_queue_timestamps]

    if not auditor_queue_sizes:
        print('No audit consumer queue size data found')
        print('')
        return

    print('Audit consumer queue size')
    print('    Latest queue size value: %s' % auditor_queue_sizes[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Items in Audit queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(auditor_queue_timestamps,
             auditor_queue_sizes,
             label='Audit')

    print(fig.show())
    print('')
    print('')


def show_grep_plugin_performance(scan):
    scan.seek(0)

    grep_plugin_times = {}

    for line in scan:
        match = GREP_PLUGIN_RE.search(line)
        if match:
            plugin_name = match.group(1)
            run_time = float(match.group(2))

            if plugin_name in grep_plugin_times:
                grep_plugin_times[plugin_name] += run_time
            else:
                grep_plugin_times[plugin_name] = run_time

    def sort_by_second(a, b):
        return cmp(b[1], a[1])

    times = grep_plugin_times.items()
    times.sort(sort_by_second)

    if not times:
        print('No grep plugins were run in this scan')

    print('Plugins run time information (in seconds)')
    print('')

    for plugin_name, total_run_time in times:
        print('%s: %.2f' % (plugin_name.ljust(25), total_run_time))


def show_queue_size_grep(scan):
    scan.seek(0)

    grep_queue_sizes = []
    grep_queue_timestamps = []

    for line in scan:
        match = GREP_DISK_DICT.search(line)
        if match:
            grep_queue_sizes.append(int(match.group(1)))
            grep_queue_timestamps.append(get_line_epoch(line))

    # Get the last timestamp to use as max in the graphs
    first_timestamp = get_first_timestamp(scan)
    last_timestamp = get_last_timestamp(scan)
    spent_time_epoch = last_timestamp - first_timestamp
    grep_queue_timestamps = [ts - first_timestamp for ts in grep_queue_timestamps]

    if not grep_queue_sizes:
        print('No grep consumer queue size data found')
        return

    print('Grep consumer queue size')
    print('    Latest queue size value: %s' % grep_queue_sizes[-1])
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.register_label_formatter(float, _num_formatter)
    fig.register_label_formatter(int, _num_formatter)
    fig.y_label = 'Items in Grep queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=spent_time_epoch)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(grep_queue_timestamps,
             grep_queue_sizes,
             label='Grep')

    print(fig.show())
    print('')
    print('')


def show_crawling_stats(scan):
    FOUND = 'A new form was found!'
    IGNORING = 'Ignoring form'
    FUZZABLE = 'New fuzzable request identified'

    scan.seek(0)
    found_forms = 0
    ignored_forms = 0
    fuzzable = 0

    for line in scan:
        if FUZZABLE in line:
            fuzzable += 1
            continue

        if FOUND in line:
            found_forms += 1
            continue

        if IGNORING in line:
            ignored_forms += 1
            continue

    print('Found %s fuzzable requests' % fuzzable)
    print('Found %s forms' % found_forms)
    print('Ignored %s forms' % ignored_forms)


def show_generic_spent_time(scan, name, must_have):
    scan.seek(0)
    spent_time = 0.0

    for line in scan:
        if must_have not in line:
            continue

        match = SCAN_TOOK_RE.search(line)
        if match:
            spent_time += float(match.group(1))

    print('    %s() took %s' % (name, epoch_to_string(spent_time)))


def show_discovery_time(scan):
    show_generic_spent_time(scan, 'discover', '.discover(')


def show_audit_time(scan):
    show_generic_spent_time(scan, 'audit', '.audit(')


def show_grep_time(scan):
    show_generic_spent_time(scan, 'grep', '.grep(')


def show_output_time(scan):
    show_generic_spent_time(scan, 'output', '.flush(')


def show_http_errors(scan):
    scan.seek(0)
    error_count = 0

    for line in scan:
        for error in HTTP_ERRORS:
            if error in line:
                error_count += 1

    print('The scan generated %s HTTP errors' % error_count)


def show_total_http_requests(scan):
    scan.seek(0)
    count = dict()
    cached_responses = 0.0

    for line in scan:

        if FROM_CACHE in line:
            cached_responses += 1

        match = HTTP_CODE_RE.search(line)
        if match:
            code = match.group(1)

            if code in count:
                count[code] += 1
            else:
                count[code] = 1

    total = sum(count.itervalues())
    print('The scan sent %s HTTP requests' % total)
    print('%i%% responses came from HTTP cache' % (cached_responses / total * 100,))

    for code, num in count.iteritems():
        print('    Sent %s HTTP requests which returned code %s' % (code, num))

    print('')


def show_known_problems(scan):
    """
    This will query the log for some known issues and if those appear show
    alerts in the output.

    :param scan: The file handler for the scan log
    :return: None, all printed to the output
    """
    scan.seek(0)

    #
    #   Identify a problem I rarely see: grep plugin finishes and other plugins
    #   are still running. This seems to be an issue in the teardown process.
    #
    found_grep_teardown = None

    grep_teardown = 'Finished Grep consumer _teardown'
    discover_call = '.discover(uri='

    for line in scan:
        if grep_teardown in line:
            found_grep_teardown = line
            continue

        if discover_call in line and found_grep_teardown:
            print('Known issue found!')
            print('')
            print('The grep consumer was finished at:')
            print('    %s' % found_grep_teardown)
            print('But calls to discover were found after:')
            print('    %s' % line)
            break


def show_freeze_locations(scan):
    """
    [Wed Nov  1 23:43:16 2017 - debug] ...
    [Wed Nov  1 23:43:19 2017 - debug] ...

    3 seconds without writing anything to the log? That is a freeze!

    :param scan: The file handler for the scan log
    :return: None, all printed to the output
    """
    scan.seek(0)
    freezes = []

    previous_line_time = get_line_epoch(scan.readline())

    for line in scan:
        try:
            current_line_epoch = get_line_epoch(line)
        except InvalidTimeStamp:
            continue

        time_spent = current_line_epoch - previous_line_time

        if time_spent > 5:
            line = line.strip()

            if len(line) >= 80:
                msg = 'Found %s second freeze at: %s...' % (time_spent, line[:80])
            else:
                msg = 'Found %s second freeze at: %s' % (time_spent, line)

            freezes.append(msg)

        previous_line_time = current_line_epoch

    if not freezes:
        print('No delays greater than 3 seconds were found between two scan log lines')
        return

    print('Found the delays greater than 3 seconds around these scan log lines:')
    for freeze in freezes:
        print('    - %s' % freeze)


class InvalidTimeStamp(Exception):
    pass


def get_line_epoch(scan_line):
    """
    [Wed Nov  1 23:43:16 2017 - debug] ...

    :param scan_line: A scan line
    :return: The time (as epoch) associated with that line
    """
    timestamp = scan_line[1:scan_line.find('-')].strip()
    try:
        parsed_time = datetime.datetime.strptime(timestamp, '%c')
    except KeyboardInterrupt:
        sys.exit(3)
    except:
        raise InvalidTimeStamp('Invalid timestamp: "%s"' % scan_line)
    else:
        return int(parsed_time.strftime('%s'))


FIRST_TIMESTAMP = None
LAST_TIMESTAMP = None


def get_first_timestamp(scan):
    # This is so ugly...
    global FIRST_TIMESTAMP

    if FIRST_TIMESTAMP is not None:
        return FIRST_TIMESTAMP

    scan.seek(0)
    line = scan.readline()
    scan.seek(0)

    timestamp = get_line_epoch(line)

    if FIRST_TIMESTAMP is None:
        FIRST_TIMESTAMP = timestamp

    return FIRST_TIMESTAMP


def get_last_timestamp(scan):
    # This is so ugly...
    global LAST_TIMESTAMP

    if LAST_TIMESTAMP is not None:
        return LAST_TIMESTAMP

    scan.seek(0)

    for line in reverse_readline(scan):
        try:
            timestamp = get_line_epoch(line)
        except InvalidTimeStamp:
            # Read one more line backwards
            continue
        else:
            break

    scan.seek(0)

    if LAST_TIMESTAMP is None:
        LAST_TIMESTAMP = timestamp

    return LAST_TIMESTAMP


def reverse_readline(fh, buf_size=8192):
    """a generator that returns the lines of a file in reverse order"""
    segment = None
    offset = 0
    fh.seek(0, os.SEEK_END)
    file_size = remaining_size = fh.tell()
    while remaining_size > 0:
        offset = min(file_size, offset + buf_size)
        fh.seek(file_size - offset)
        buffer = fh.read(min(remaining_size, buf_size))
        remaining_size -= buf_size
        lines = buffer.split('\n')
        # the first line of the buffer is probably not a complete line so
        # we'll save it and append it to the last line of the next buffer
        # we read
        if segment is not None:
            # if the previous chunk starts right from the beginning of line
            # do not concact the segment to the last line of new chunk
            # instead, yield the segment first
            if buffer[-1] is not '\n':
                lines[-1] += segment
            else:
                yield segment
        segment = lines[0]
        for index in range(len(lines) - 1, 0, -1):
            if len(lines[index]):
                yield lines[index]
    # Don't yield None if the file was empty
    if segment is not None:
        yield segment


def make_relative_timestamps(timestamps, first_timestamp):
    """
    Take a list of timestamps (which are in epoch format) and make them
    relative to the scan start time.

    :param timestamps: List of timestamps
    :param first_timestamp: The scan started here
    :return: A list of timestamps relative to the first_timestamp
    """
    return [t - first_timestamp for t in timestamps]


def watch(scan, function_name):
    scan.seek(0)

    while True:
        clear_screen()

        try:
            # Hack me here
            globals()[function_name](scan)
            time.sleep(5)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception, e:
            print('Exception: %s' % e)
            sys.exit(1)


def clear_screen():
    os.system('clear')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='w3af scan log analyzer', usage=HELP)

    parser.add_argument('scan_log', action='store')
    parser.add_argument('--watch', action='store', dest='watch',
                        help='Show only one graph and refresh every 5 seconds.')

    parsed_args = parser.parse_args()

    try:
        scan = file(parsed_args.scan_log)
    except:
        print('The scan log file does not exist!')
        sys.exit(2)

    if parsed_args.watch:
        watch(scan, parsed_args.watch)
    else:
        show_scan_stats(scan)
