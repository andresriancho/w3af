#!/usr/bin/env python

import re
import sys
import datetime
import dateutil.parser

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

GREP_DISK_DICT = re.compile('from disk. The current Grep DiskDict size is (\d*).')
AUDITOR_DISK_DICT = re.compile('from disk. The current Auditor DiskDict size is (\d*).')
CRAWLINFRA_DISK_DICT = re.compile('from disk. The current CrawlInfra DiskDict size is (\d*).')

RTT_RE = re.compile('\(.*?rtt=(.*?),.*\)')

HTTP_ERRORS = ('Failed to HTTP',
               'Raising HTTP error')


def epoch_to_string(spent_time):
    time_delta = datetime.timedelta(seconds=spent_time)

    weeks, days = divmod(time_delta.days, 7)

    minutes, seconds = divmod(time_delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)

    msg = ''

    if weeks == days == hours == minutes == seconds == 0:
        msg += '0 seconds.'
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
        msg += '.'

    return msg


def show_scan_stats(scan):
    show_scan_finished_in(scan)

    print('')

    show_discovery_time(scan)
    show_audit_time(scan)
    show_grep_time(scan)
    show_output_time(scan)

    print('')

    show_http_errors(scan)
    show_total_http_requests(scan)
    show_rtt_histo(scan)
    show_timeout(scan)
    show_http_requests_over_time(scan)

    print('')

    show_findings_stats(scan)

    print('')

    show_queue_size(scan)

    print('')

    show_freeze_locations(scan)


def show_scan_finished_in(scan):
    scan.seek(0)

    for line in scan:
        match = SCAN_FINISHED_IN.search(line)
        if match:
            print(match.group(0))
            break


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

    for line in scan:
        match = SOCKET_TIMEOUT.search(line)
        if match:
            timeouts.append(float(match.group(1)))

    print('Socket timeout over time')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Socket timeout'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=None)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(xrange(len(timeouts)),
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


def show_queue_size(scan):
    scan.seek(0)

    grep_queue_sizes = []
    auditor_queue_sizes = []
    crawl_queue_sizes = []

    for line in scan:
        match = GREP_DISK_DICT.search(line)
        if match:
            grep_queue_sizes.append(int(match.group(1)))

        match = AUDITOR_DISK_DICT.search(line)
        if match:
            auditor_queue_sizes.append(int(match.group(1)))

        match = CRAWLINFRA_DISK_DICT.search(line)
        if match:
            crawl_queue_sizes.append(int(match.group(1)))

    print('Consumer queue sizes')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Items in Audit queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=None)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(xrange(len(auditor_queue_sizes)),
             auditor_queue_sizes,
             label='Audit')

    print(fig.show())
    print('')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Items in CrawlInfra queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=None)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(xrange(len(crawl_queue_sizes)),
             crawl_queue_sizes,
             label='Crawl')

    print(fig.show())
    print('')
    print('')

    fig = plotille.Figure()
    fig.width = 90
    fig.height = 20
    fig.y_label = 'Items in Grep queue'
    fig.x_label = 'Time'
    fig.color_mode = 'byte'
    fig.set_x_limits(min_=0, max_=None)
    fig.set_y_limits(min_=0, max_=None)

    fig.plot(xrange(len(grep_queue_sizes)),
             grep_queue_sizes,
             label='Grep')

    print(fig.show())
    print('')
    print('')


def show_findings_stats(scan):
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

    print('%s() took %s' % (name, epoch_to_string(spent_time)))


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

    previous_line_time = get_line_epoch(scan.readline())

    for line in scan:
        try:
            current_line_epoch = get_line_epoch(line)
        except InvalidTimeStamp:
            continue

        time_spent = current_line_epoch - previous_line_time

        if time_spent > 5:
            line = line.strip()
            print('Found %s second freeze at: %s...' % (time_spent, line[:80]))

        previous_line_time = current_line_epoch


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
        parsed_time = dateutil.parser.parse(timestamp)
    except KeyboardInterrupt:
        sys.exit(3)
    except:
        raise InvalidTimeStamp
    else:
        return int(parsed_time.strftime('%s'))


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
