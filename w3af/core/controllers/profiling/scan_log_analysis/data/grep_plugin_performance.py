import re

GREP_PLUGIN_RE = re.compile('\] (.*?).grep\(uri=".*"\) took (.*?)s to run')


def show_grep_plugin_performance(scan_log_filename, scan):
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

    times_top_10 = times[:10]
    times_top_10 = sum(total_run_time for plugin_name, total_run_time in times_top_10)

    if not times:
        print('No grep plugins were run in this scan')

    print('Top10 most time consuming plugins took %s seconds to run' % times_top_10)
    print('')

    print('Plugins run time information (in seconds)')
    print('')

    for plugin_name, total_run_time in times:
        print('%s: %.2f' % (plugin_name.ljust(25), total_run_time))
