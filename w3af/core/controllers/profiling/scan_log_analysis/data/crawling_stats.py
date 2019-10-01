import re

from utils.output import ListOutput, ListOutputItem


NEW_URL_FOUND = re.compile('New URL found by (.*?) plugin')


def get_crawling_stats(scan_log_filename, scan):
    FOUND = 'A new form was found!'
    IGNORING = 'Ignoring form'
    FUZZABLE = 'New fuzzable request identified'

    output = ListOutput('crawl_stats')

    scan.seek(0)

    found_forms = 0
    ignored_forms = 0
    fuzzable = 0
    new_url_found_by_plugin = {}

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

        match = NEW_URL_FOUND.search(line)
        if match:
            plugin_name = match.group(1)
            if plugin_name in new_url_found_by_plugin:
                new_url_found_by_plugin[plugin_name] += 1
            else:
                new_url_found_by_plugin[plugin_name] = 1

    output.append(ListOutputItem('fuzzable requests', {'found': fuzzable}))
    output.append(ListOutputItem('forms', {'found': found_forms,
                                           'ignored': ignored_forms}))

    if not new_url_found_by_plugin:
        return

    output.append(ListOutputItem('found URLs (group by plugin)', new_url_found_by_plugin))

    return output
