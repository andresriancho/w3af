import re

from utils.output import KeyValueOutput


FINISHED_BRUTEFORCE = [re.compile('Finished bruteforcing ".*?" \(spent (.*?)\)'),
                       re.compile('Finished basic authentication bruteforce on ".*?" \(spent (.*?)\)')]


def get_bruteforce_data(scan_log_filename, scan):
    scan.seek(0)

    times = []

    for line in scan:
        if 'brute' not in line:
            continue

        for finished_re in FINISHED_BRUTEFORCE:
            match = finished_re.search(line)
            if match:
                took = match.group(1)
                times.append(took)

    output = KeyValueOutput('bruteforce_performance',
                            'Time spent brute-forcing',
                            {'count': len(times),
                             'times': times})

    return output
