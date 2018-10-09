import re

from utils.utils import get_path

WEBSPIDER_FOUND_LINK = re.compile('\[web_spider\] Found new link "(.*?)" at "(.*?)"')


def generate_crawl_graph(scan_log_filename, scan):
    scan.seek(0)

    data = {}

    for line in scan:
        match = WEBSPIDER_FOUND_LINK.search(line)
        if not match:
            continue
        new_link = get_path(match.group(1))
        referer = get_path(match.group(2))
        if referer in data:
            data[referer].append(new_link)
        else:
            data[referer] = [new_link]

    if not data:
        print('No web_spider data found!')

    def sort_by_len(a, b):
        return cmp(len(a), len(b))

    referers = data.keys()
    referers.sort(sort_by_len)

    print('')
    print('web_spider crawling data (source -> new link)')

    previous_referer = None

    for referer in referers:
        new_links = data[referer]
        new_links.sort(sort_by_len)
        for new_link in new_links:
            if referer is previous_referer:
                spaces = ' ' * len('%s -> ' % previous_referer)
                print('%s%s' % (spaces, new_link))
            else:
                print('%s -> %s' % (referer, new_link))
                previous_referer = referer

    print('')
