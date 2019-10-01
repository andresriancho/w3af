import os
import sys
import datetime

from urlparse import urlparse


FIRST_TIMESTAMP = None
LAST_TIMESTAMP = None


def get_path(url):
    return urlparse(url).path


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
    """
    a generator that returns the lines of a file in reverse order
    """
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


def clear_screen():
    os.system('clear')


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
