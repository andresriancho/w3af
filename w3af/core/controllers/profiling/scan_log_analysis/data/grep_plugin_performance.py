import re

from utils.output import ListOutput, ListOutputItem

GREP_PLUGIN_RE = re.compile('\] (.*?).grep\(uri=".*"\) took (.*?)s to run')


def get_grep_plugin_performance(scan_log_filename, scan):
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

    output = ListOutput('grep_plugin_performance')

    output.append(ListOutputItem('Top10 most time consuming plugins run for (seconds)', times_top_10))

    times = dict(times)
    output.append(ListOutputItem('Plugins run time information (in seconds)', times))

    return output
