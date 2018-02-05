#!/usr/bin/env python

import re
import sys
import datetime

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
'''
SCAN_FINISHED_IN = re.compile('Scan finished in (.*).')

SCAN_TOOK_RE = re.compile('took (\d*\.\d\d)s to run')

HTTP_CODE_RE = re.compile('returned HTTP code "(.*?)"')
FROM_CACHE = 'from_cache=1'

SOCKET_TIMEOUT = re.compile('Updating socket timeout for .* from .* to (.*?) seconds')

GREP_DISK_DICT = re.compile('The current Grep DiskDict size is (\d*).')
AUDITOR_DISK_DICT = re.compile('The current Auditor DiskDict size is (\d*).')
CRAWLINFRA_DISK_DICT = re.compile('The current CrawlInfra DiskDict size is (\d*).')

RTT_RE = re.compile('\(.*?rtt=(.*?),.*\)')

ERRORS_RE = [re.compile('Unhandled exception "(.*?)"'),
             re.compile('traceback', re.IGNORECASE),
             re.compile('scan was able to continue by ignoring those'),
             re.compile('The scan will stop')]

HTTP_ERRORS = ('Failed to HTTP',
               'Raising HTTP error')

WORKER_POOL_SIZE = re.compile('the worker pool size to (.*?) ')
ACTIVE_THREADS = re.compile('The framework has (.*?) active threads.')

JOIN_TIMES = re.compile('(.*?) took (.*?) seconds to join\(\)')

CONNECTION_POOL_WAIT = re.compile('Waited (.*?)s for a connection to be available in the pool.')

IDLE_CONSUMER_WORKERS = re.compile('\[.*? - .*?\] (.*?)% of (.*?) workers are idle.')


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
    show_connection_pool_wait(scan)
    show_http_requests_over_time(scan)

    print('')

    show_crawling_stats(scan)

    print('')

    show_queue_size_grep(scan)
    show_queue_size_audit(scan)
    show_queue_size_crawl(scan)

    print('')

    show_worker_pool_size(scan)
    show_active_threads(scan)
    show_consumer_pool_size(scan)

    print('')

    show_consumer_join_times(scan)

    print('')

    show_freeze_locations(scan)


def show_active_threads(scan):
    scan.seek(0)

    active_threads = []
    active_threads_timestamps = []

    for line in scan:
        match = ACTIVE_THREADS.search(line)
        if match:
            active_threads.append(float(match.group(1)))
            active_threads_timestamps.append(get_line_epoch(line))

    last_timestamp = get_line_epoch(line)

    if not active_threads:
        print('No active thread data found')
        return

    print('Active thread count over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Thread count'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=active_threads_timestamps[0], max_=last_timestamp)
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

    last_timestamp = get_line_epoch(line)

    if not connection_pool_waits:
        print('No connection pool wait data found')
        return

    print('Time waited for worker threads for an available TCP/IP connection')
    print('    Total: %.2f sec' % sum(connection_pool_waits))
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Waited time'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=connection_pool_timestamps[0], max_=last_timestamp)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(connection_pool_timestamps,
             connection_pool_waits)

    print(fig.show())
    print('')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Count'
    fig.x_label = 'Time waiting for available TCP/IP connection'
    fig.set_x_limits(min_=0)
    fig.set_y_limits(min_=0)
    fig.color_mode = 'byte'

    fig.histogram(connection_pool_waits, bins=60)

    print(fig.show())
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

    for line in scan:
        match = IDLE_CONSUMER_WORKERS.search(line)
        if not match:
            continue

        percent = int(match.group(1))
        is_audit = 'audit' in match.group(2).lower()

        if is_audit:
            consumer_pool_perc_audit.append(percent)
            consumer_pool_timestamps_audit.append(get_line_epoch(line))
        else:
            consumer_pool_perc_crawl.append(percent)
            consumer_pool_timestamps_crawl.append(get_line_epoch(line))

    last_timestamp = get_line_epoch(line)

    if not consumer_pool_perc_audit and not consumer_pool_perc_crawl:
        print('No consumer pool data found')
        return

    print('Idle consumer pool workers over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Idle worker (%)'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=consumer_pool_timestamps_audit[0], max_=last_timestamp)
    fig.set_y_limits(min_=0, max_=100)

    fig.plot(consumer_pool_timestamps_audit,
             consumer_pool_perc_audit,
             label='Idle audit workers',
             lc=100)

    fig.plot(consumer_pool_timestamps_crawl,
             consumer_pool_perc_crawl,
             label='Idle crawl workers',
             lc=200)

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

    last_timestamp = get_line_epoch(line)

    if not worker_pool_sizes:
        print('No worker pool size data found')
        return

    print('Worker pool size over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Worker pool size'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=worker_pool_timestamps[0], max_=last_timestamp)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(worker_pool_timestamps,
             worker_pool_sizes,
             label='Workers')

    print(fig.show())
    print('')
    print('')


def show_scan_finished_in(scan):
    scan.seek(0)

    first_line_epoch = get_line_epoch(scan.readline())

    for line in scan:
        match = SCAN_FINISHED_IN.search(line)
        if match:
            print(match.group(0))
            return

    last_line_epoch = get_line_epoch(line)

    scan_run_time = last_line_epoch - first_line_epoch
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

    last_timestamp = get_line_epoch(line)

    if not timeouts:
        print('No socket timeout data found')
        return

    print('Socket timeout over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Socket timeout'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=timeout_timestamps[0], max_=last_timestamp)
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
    fig.y_label = 'Count'
    fig.x_label = 'RTT'
    fig.set_x_limits(min_=0)
    fig.set_y_limits(min_=0)
    fig.color_mode = 'byte'

    fig.histogram(rtts, bins=60)

    print('')
    print('RTT Histogram')
    print(fig.show())


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
    last_timestamp = get_line_epoch(line)

    if not crawl_queue_sizes:
        print('No crawl consumer queue size data found')
        return

    print('Crawl consumer queue size')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Items in CrawlInfra queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=crawl_queue_timestamps[0], max_=last_timestamp)
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
    last_timestamp = get_line_epoch(line)

    if not auditor_queue_sizes:
        print('No audit consumer queue size data found')
        return

    print('Audit consumer queue size')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Items in Audit queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=auditor_queue_timestamps[0], max_=last_timestamp)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(auditor_queue_timestamps,
             auditor_queue_sizes,
             label='Audit')

    print(fig.show())
    print('')
    print('')


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
    last_timestamp = get_line_epoch(line)

    if not grep_queue_sizes:
        print('No audit consumer queue size data found')
        return

    print('Grep consumer queue sizes')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Items in Grep queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=grep_queue_timestamps[0], max_=last_timestamp)
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
            freezes.append('Found %s second freeze at: %s...' % (time_spent, line[:80]))

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
        raise InvalidTimeStamp
    else:
        return int(parsed_time.strftime('%s'))


def make_relative_timestamps(timestamps, first_timestamp):
    """
    Take a list of timestamps (which are in epoch format) and make them
    relative to the scan start time.

    :param timestamps: List of timestamps
    :param first_timestamp: The scan started here
    :return: A list of timestamps relative to the first_timestamp
    """
    return [t - first_timestamp for t in timestamps]


if __name__ == '__main__':
    try:
        # pylint: disable=E0632
        _, scan = sys.argv
        # pylint: enable=E0632
    except:
        print(HELP)
        sys.exit(1)

    try:
        scan = file(scan)
    except:
        print(HELP)
        sys.exit(2)

    show_scan_stats(scan)
