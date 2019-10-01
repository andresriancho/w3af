import re

from utils.utils import epoch_to_string
from utils.output import KeyValueOutput
from utils.output import ListOutput, ListOutputItem

SCAN_TOOK_RE = re.compile('took (\d*\.\d\d)s to run')
PLUGIN_TOOK_RE = re.compile('\] (.*?)\.(grep|audit|discover)\(.*?\) took (.*?)s to run')


def show_generic_spent_time(scan, name, must_have):
    scan.seek(0)
    spent_time = 0.0

    for line in scan:
        if must_have not in line:
            continue

        match = SCAN_TOOK_RE.search(line)
        if match:
            spent_time += float(match.group(1))

    return KeyValueOutput('%s_spent_time' % name,
                          'Time spent running %s plugins' % name,
                          {'human': epoch_to_string(spent_time),
                           'seconds': spent_time})


def get_plugin_time(scan_log_filename, scan):
    scan.seek(0)
    spent_time_by_plugin = dict()

    for line in scan:
        if 'took' not in line:
            continue

        match = PLUGIN_TOOK_RE.search(line)
        if not match:
            continue

        plugin_name = match.group(1)
        plugin_type = match.group(2)
        took = float(match.group(3))

        if plugin_type not in spent_time_by_plugin:
            spent_time_by_plugin[plugin_type] = {}
            spent_time_by_plugin[plugin_type][plugin_name] = took

        elif plugin_name not in spent_time_by_plugin[plugin_type]:
            spent_time_by_plugin[plugin_type][plugin_name] = took

        else:
            spent_time_by_plugin[plugin_type][plugin_name] += took

    if not spent_time_by_plugin:
        return

    output = ListOutput('plugin_wall_clock_stats')

    def sort_by_value(a, b):
        return cmp(b[1], a[1])

    for plugin_type in spent_time_by_plugin:
        spent_time_by_plugin_one_type = spent_time_by_plugin[plugin_type]

        spent_time_items = spent_time_by_plugin_one_type.items()
        spent_time_items.sort(sort_by_value)
        spent_time_items = spent_time_items[:15]
        spent_time_dict = dict(spent_time_items)

        # round
        spent_time_dict = dict((plugin_name, round(took)) for plugin_name, took in spent_time_dict.iteritems())

        title = 'Top10 wall time used by %s plugins (seconds)'
        output.append(ListOutputItem(title % plugin_type, spent_time_dict))

    return output


def get_discovery_time(scan_log_filename, scan):
    return show_generic_spent_time(scan, 'discover', '.discover(')


def get_audit_time(scan_log_filename, scan):
    return show_generic_spent_time(scan, 'audit', '.audit(')


def get_grep_time(scan_log_filename, scan):
    return show_generic_spent_time(scan, 'grep', '.grep(')


def get_output_time(scan_log_filename, scan):
    return show_generic_spent_time(scan, 'output', '.flush(')
