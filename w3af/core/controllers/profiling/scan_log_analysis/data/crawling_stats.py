import re

NEW_URL_FOUND = re.compile('New URL found by (.*?) plugin')


def show_crawling_stats(scan):
    FOUND = 'A new form was found!'
    IGNORING = 'Ignoring form'
    FUZZABLE = 'New fuzzable request identified'

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

    print('Found %s fuzzable requests' % fuzzable)
    print('Found %s forms' % found_forms)
    print('Ignored %s forms' % ignored_forms)

    if not new_url_found_by_plugin:
        return

    print('')
    print('URLs found grouped by plugin:')

    def by_value(a, b):
        return cmp(b[1], a[1])

    nufbp = new_url_found_by_plugin.items()
    nufbp.sort(by_value)

    for plugin_name, count in nufbp:
        print('    - %s: %s' % (plugin_name, count))
