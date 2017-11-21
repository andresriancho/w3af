#!/usr/bin/env python

import re
import sys
import time
import datetime
import dateutil.parser

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

SCAN_TOOK_RE = re.compile('took (.*?) seconds to run')


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
            msg += str(
                minutes) + ' minute%s ' % ('s' if minutes > 1 else '')
        if seconds:
            msg += str(
                seconds) + ' second%s' % ('s' if seconds > 1 else '')
        msg += '.'

    return msg


def show_scan_stats(scan):
    show_discovery_time(scan)
    show_audit_time(scan)
    show_grep_time(scan)
    show_output_time(scan)
    show_total_http_requests(scan)
    show_freeze_locations(scan)


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


def show_total_http_requests(scan):
    scan.seek(0)
    count = 0

    for line in scan:
        if 'returned HTTP code' in line:
            count += 1

    print('The scan sent %s HTTP requests' % count)


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
        _, scan = sys.argv
    except:
        print(HELP)
        sys.exit(1)

    try:
        scan = file(scan)
    except:
        print(HELP)
        sys.exit(2)

    show_scan_stats(scan)
