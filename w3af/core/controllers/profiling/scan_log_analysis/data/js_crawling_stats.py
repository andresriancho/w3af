import re

from utils.output import ListOutput, ListOutputItem
from utils.dotdict import dotdict


HTTP_REQUESTS_IN_PROXY = re.compile('Extracted (.*?) new HTTP requests from (.*?) using .*?')
CRAWL_TIME_BY_STRATEGY = re.compile('Spent (.*?) seconds in crawl strategy (.*?) for (.*?)')
CHROME_POOL_WAIT_TIME = re.compile('Spent (.*?) seconds getting a chrome instance')
INITIAL_CHROME_PAGE_LOAD = re.compile('Spent (.*?) seconds loading URL (.*?) in chrome')
PAGE_LOAD_FAIL = re.compile('Chrome did not successfully load (.*?) in (.*?) seconds')
EVENT_DISPATCH = re.compile('Dispatching "(.*?)" on CSS selector "(.*?)" at page (.*?)')

REQUIRED_START_WITH = [
    'Extracted',
    'Spent',
    'Chrome',
    'Dispatching'
]


HANDLERS = {
    HTTP_REQUESTS_IN_PROXY: 'http_requests_in_proxy_handler',
    CRAWL_TIME_BY_STRATEGY: 'crawl_time_by_strategy_handler',
    CHROME_POOL_WAIT_TIME: 'chrome_pool_wait_time_handler',
    INITIAL_CHROME_PAGE_LOAD: 'initial_chrome_page_load_handler',
    PAGE_LOAD_FAIL: 'page_load_fail_handler',
    EVENT_DISPATCH: 'event_dispatch_handler',
}


def get_js_crawling_stats(scan_log_filename, scan):
    output = ListOutput('js_crawl_stats')

    scan.seek(0)

    context = dotdict()

    context.http_requests_in_proxy = dict()
    context.js_crawl_strategy_times = list()
    context.dom_dump_crawl_strategy_times = list()
    context.chrome_pool_wait_times = list()
    context.chrome_page_load_times = list()
    context.page_load_fails = list()
    context.event_dispatch = list()

    # Get the function pointers
    for regex, handler_name in HANDLERS.iteritems():
        HANDLERS[regex] = globals()[handler_name]

    # Process all the lines
    for line in scan:

        # Performance improvement
        should_grep = False

        for required_start_with in REQUIRED_START_WITH:
            if line.startswith(required_start_with):
                should_grep = True
                break

        if not should_grep:
            continue

        # Actual information extraction
        for regex, handler_func in HANDLERS.iteritems():
            mo = regex.search(line)

            if not mo:
                continue

            handler_func(context, mo)
            break

    #
    # Now we do some post-processing with the captured data
    #

    #
    # Total number of HTTP requests sent via proxy
    #
    total_http_requests_proxy = 0

    for url, request_count in context.http_requests_in_proxy.iteritems():
        total_http_requests_proxy += request_count

    # URL with more HTTP requests
    def sort_by_second(a, b):
        return cmp(a[1], b[1])

    url_count_items = context.http_requests_in_proxy.items()
    url_count_items.sort(sort_by_second)
    url_count_items.reverse()
    url_count_items = url_count_items[:10]

    output.append(ListOutputItem('Proxied HTTP requests', {'scan total': total_http_requests_proxy,
                                                           'max by URL': url_count_items}))

    #
    # Crawl times by strategy
    #
    crawl_time_js_total = 0
    crawl_time_dom_total = 0

    for spent, url in context.js_crawl_strategy_times:
        crawl_time_js_total += spent

    for spent, url in context.dom_dump_crawl_strategy_times:
        crawl_time_dom_total += spent

    def sort_by_first(a, b):
        return cmp(a[0], b[0])

    js_max_by_url = context.js_crawl_strategy_times[:]
    js_max_by_url.sort(sort_by_first)
    js_max_by_url = js_max_by_url[:10]

    dom_dump_max_by_url = context.js_crawl_strategy_times[:]
    dom_dump_max_by_url.sort(sort_by_first)
    dom_dump_max_by_url.reverse()
    dom_dump_max_by_url = dom_dump_max_by_url[:10]

    data = {'Total': crawl_time_js_total,
            'Top 10 most time consuming by URL': js_max_by_url,
            'Average': 'n/a' if not len(context.js_crawl_strategy_times) else crawl_time_js_total / len(context.js_crawl_strategy_times)}
    output.append(ListOutputItem('JS crawl times (seconds)', data))

    data = {'Total': crawl_time_dom_total,
            'Top 10 most time consuming by URL': dom_dump_max_by_url,
            'Average': 'n/a' if not len(context.dom_dump_crawl_strategy_times) else crawl_time_dom_total / len(context.dom_dump_crawl_strategy_times)}
    output.append(ListOutputItem('DOM dump crawl times (seconds)', data))

    #
    # Pool wait times
    #
    pool_wait_time_total = sum(context.chrome_pool_wait_times)

    data = {'Total': pool_wait_time_total,
            'Average': 'n/a' if not len(context.chrome_pool_wait_times) else pool_wait_time_total / len(context.chrome_pool_wait_times)}
    output.append(ListOutputItem('Initial page load', data))

    #
    # Initial page load times
    #
    initial_page_load_total = 0

    for spent, url in context.chrome_page_load_times:
        initial_page_load_total += spent

    page_load_max_by_url = context.chrome_page_load_times[:]
    page_load_max_by_url.sort(sort_by_first)
    page_load_max_by_url.reverse()
    page_load_max_by_url = page_load_max_by_url[:10]

    data = {'Total': initial_page_load_total,
            'Top 10 most time consuming by URL': page_load_max_by_url,
            'Average': 'n/a' if not len(context.chrome_page_load_times) else initial_page_load_total / len(context.chrome_page_load_times)}
    output.append(ListOutputItem('Initial page load', data))

    #
    # Page load fail
    #
    total_page_load_fail = len(context.page_load_fails)

    data = {'Total': total_page_load_fail}
    output.append(ListOutputItem('Page load fail', data))

    #
    # Dispatched events
    #
    most_common_events = {}
    pages_with_most_events = {}
    most_common_selector = {}

    for event, selector, url in context.event_dispatch:
        if event not in most_common_events:
            most_common_events[event] = 1
        else:
            most_common_events[event] += 1

        if url not in pages_with_most_events:
            pages_with_most_events[url] = 1
        else:
            pages_with_most_events[url] += 1

        if selector not in most_common_selector:
            most_common_selector[selector] = 1
        else:
            most_common_selector[selector] += 1

    most_common_selector = most_common_selector.items()
    most_common_selector.sort(sort_by_second)
    most_common_selector.reverse()
    most_common_selector = most_common_selector[:10]

    most_common_events = most_common_events.items()
    most_common_events.sort(sort_by_second)
    most_common_events.reverse()
    most_common_events = most_common_events[:10]

    pages_with_most_events = pages_with_most_events.items()
    pages_with_most_events.sort(sort_by_second)
    pages_with_most_events.reverse()
    pages_with_most_events = pages_with_most_events[:10]

    output.append(ListOutputItem('Most common selectors', most_common_selector))
    output.append(ListOutputItem('Pages with most events', pages_with_most_events))
    output.append(ListOutputItem('Most common events', most_common_events))

    return output


def http_requests_in_proxy_handler(context, match_object):
    count = match_object.group(1)
    count = int(count)

    url = match_object.group(2)

    if url in context.http_requests_in_proxy:
        context.http_requests_in_proxy[url] += count
    else:
        context.http_requests_in_proxy[url] = count


def crawl_time_by_strategy_handler(context, match_object):
    seconds = match_object.group(1)
    seconds = float(seconds)

    strategy = match_object.group(2)

    url = match_object.group(3)

    if strategy == 'JS events':
        context.js_crawl_strategy_times.append((seconds, url))
    else:
        context.dom_dump_crawl_strategy_times.append((seconds, url))


def chrome_pool_wait_time_handler(context, match_object):
    seconds = match_object.group(1)
    seconds = float(seconds)

    context.chrome_pool_wait_times.append(seconds)


def initial_chrome_page_load_handler(context, match_object):
    url = match_object.group(2)

    seconds = match_object.group(1)
    seconds = float(seconds)

    context.chrome_page_load_times.append((seconds, url))


def page_load_fail_handler(context, match_object):
    url = match_object.group(1)

    seconds = match_object.group(2)
    seconds = float(seconds)

    context.page_load_fails.append((url, seconds))


def event_dispatch_handler(context, match_object):
    event = match_object.group(1)
    selector = match_object.group(2)
    url = match_object.group(3)

    context.event_dispatch.append((event, selector, url))
