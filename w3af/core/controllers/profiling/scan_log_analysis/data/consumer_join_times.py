import re


JOIN_TIMES = re.compile('(.*?) took (.*?) seconds to join\(\)')


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