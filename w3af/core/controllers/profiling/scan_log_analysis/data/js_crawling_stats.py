import re
import json

from utils.output import ListOutput, ListOutputItem
from utils.dotdict import dotdict


CRAWL_TIME_BY_STRATEGY = re.compile('Spent (.*?) seconds in crawl strategy (.*?) for (.*?) \(did:')

EVENT_IGNORE = re.compile('Ignoring "(.*?)" event on selector "(.*?)" and URL "(.*?)"')
EVENT_DISPATCH_STATS = re.compile(r'Event dispatch error count is (.*?). Already processed (.*?) events with types: (.*?)\. \(did:')

EXTRACTED_HTTP_REQUESTS = re.compile(r'Extracted (.*?) new HTTP requests from (.*?)')
TOTAL_CHROME_PROXY_REQUESTS = re.compile(r'A total of (.*?) HTTP requests have been read by the web_spider')

SECONDS_LOADING_URL = re.compile(r'Spent (.*?) seconds loading URL (.*?)')
WAIT_FOR_LOAD_TIMEOUTS = re.compile(r'wait_for_load\(timeout=(.*?)\) timed out')

CHROME_POOL_PERF = re.compile(r'ChromePool.get\(\) took (.*?) seconds to create an instance')
WEBSOCKET_MESSAGE_WAIT_TIME = re.compile(r'Waited (.*?) seconds for message with ID')
CHROME_CRAWLER_STATUS = re.compile(r'ChromeCrawler status ((.*?) running tasks, (.*?) workers, (.*?) tasks in queue)')

REGEX_NAMES = {
    'CRAWL_TIME_BY_STRATEGY',
    'EVENT_IGNORE',
    'EVENT_DISPATCH_STATS',
    'EXTRACTED_HTTP_REQUESTS',
    #'SECONDS_LOADING_URL',
    #'CHROME_POOL_PERF',
    #'TOTAL_CHROME_PROXY_REQUESTS',
    #'WEBSOCKET_MESSAGE_WAIT_TIME',
    #'WAIT_FOR_LOAD_TIMEOUTS',
    #'CHROME_CRAWLER_STATUS'
}

REQUIRED_TEXT = [
    'Spent',
    'Ignoring',
    'dispatch',
    'Extracted',
    'ChromePool',
    'A total of',
    'for message with ID',
    'wait_for_load',
    'ChromeCrawler',
]


HANDLERS = dict()


def get_js_crawling_stats(scan_log_filename, scan):
    """
    Main entry point for this analyzer

    :param scan_log_filename: The name of the scan log file
    :param scan: The file descriptor for the scan log
    :return: The output
    """
    populate_handlers()

    output = ListOutput('js_crawl_stats')

    context = read_data(scan)
    post_process_context(context, output)

    return output


def should_grep(line):
    for required_text in REQUIRED_TEXT:
        if required_text in line:
            return True

    return False


def get_handler_name(regex_name):
    return '%s_handler' % regex_name.lower()


def populate_handlers():
    for regex_name in REGEX_NAMES:
        HANDLERS[globals()[regex_name]] = globals()[get_handler_name(regex_name)]


def sort_by_first(a, b):
    return cmp(a[0], b[0])


def sort_by_second(a, b):
    return cmp(a[1], b[1])


def read_data(scan):
    scan.seek(0)

    context = dotdict()

    context.js_crawl_strategy_times = list()
    context.dom_dump_crawl_strategy_times = list()
    context.event_ignore = list()
    context.event_dispatch_stats = list()
    context.extracted_http_requests = list()

    context.http_requests_in_proxy = dict()
    context.chrome_pool_wait_times = list()
    context.chrome_page_load_times = list()
    context.page_load_fails = list()

    # Process all the lines
    for line in scan:

        # Performance improvement
        if not should_grep(line):
            continue

        # Actual information extraction
        for regex, handler_func in HANDLERS.iteritems():
            mo = regex.search(line)

            if not mo:
                continue

            handler_func(context, mo)
            break

    return context


def post_process_context(context, output):
    """
    Do some post-processing with the captured data
    """
    post_process_crawl_time_by_strategy(context, output)
    post_process_event_dispatch_stats(context, output)
    post_process_extracted_http_requests(context, output)

    post_process_http_requests_in_proxy(context, output)
    post_process_pool_wait_times(context, output)
    post_process_page_load_fail(context, output)


def post_process_extracted_http_requests(context, output):
    max_extracted_http_requests = max(context.extracted_http_requests)
    min_extracted_http_requests = min(context.extracted_http_requests)

    avg_extracted_http_requests = 0

    if len(context.extracted_http_requests):
        avg_extracted_http_requests = sum(context.extracted_http_requests) / len(context.extracted_http_requests)

    data = {'max_extracted_http_requests': max_extracted_http_requests,
            'min_extracted_http_requests': min_extracted_http_requests,
            'avg_extracted_http_requests': avg_extracted_http_requests}

    output.append(ListOutputItem('Extracted HTTP requests', data))


def post_process_event_dispatch_stats(context, output):
    ignored = len(context.event_ignore)

    dispatch_error_count, processed, by_type = context.event_dispatch_stats[-1]

    data = {'total_dispatch_errors': dispatch_error_count,
            'total_processed_events': processed,
            'events_by_type': json.dumps(by_type),
            'total_ignored': ignored}

    output.append(ListOutputItem('Dispatch stats', data))


def post_process_http_requests_in_proxy(context, output):
    #
    # Total number of HTTP requests sent via proxy
    #
    total_http_requests_proxy = 0

    for url, request_count in context.http_requests_in_proxy.iteritems():
        total_http_requests_proxy += request_count

    url_count_items = context.http_requests_in_proxy.items()
    url_count_items.sort(sort_by_second)
    url_count_items.reverse()
    url_count_items = url_count_items[:10]

    output.append(ListOutputItem('Proxied HTTP requests', {'scan total': total_http_requests_proxy,
                                                           'max by URL': url_count_items}))


def post_process_crawl_time_by_strategy(context, output):
    """
    Crawl times by strategy
    """
    crawl_time_js_total = 0
    crawl_time_dom_total = 0

    for spent, url in context.js_crawl_strategy_times:
        crawl_time_js_total += spent

    for spent, url in context.dom_dump_crawl_strategy_times:
        crawl_time_dom_total += spent

    js_max_by_url = context.js_crawl_strategy_times[:]
    js_max_by_url.sort(sort_by_first)
    js_max_by_url.reverse()
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


def post_process_pool_wait_times(context, output):
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


def post_process_page_load_fail(context, output):
    #
    # Page load fail
    #
    total_page_load_fail = len(context.page_load_fails)

    data = {'Total': total_page_load_fail}
    output.append(ListOutputItem('Page load fail', data))


def post_process_dispatched_events(context, output):
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
    elif strategy == 'DOM dump':
        context.dom_dump_crawl_strategy_times.append((seconds, url))
    else:
        raise RuntimeError('Unknown strategy: "%s"' % strategy)


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


def event_dispatch_stats_handler(context, match_object):
    dispatch_error_count = match_object.group(1)
    processed = match_object.group(2)
    by_type = match_object.group(3)

    dispatch_error_count = int(dispatch_error_count)
    processed = int(processed)

    by_type = by_type.replace("u'", "'")
    by_type = by_type.replace("'", '"')
    by_type = json.loads(by_type)

    context.event_dispatch_stats.append((dispatch_error_count, processed, by_type))


def event_ignore_handler(context, match_object):
    event_type = match_object.group(1)
    selector = match_object.group(2)
    url = match_object.group(3)

    context.event_ignore.append((event_type, selector, url))


def extracted_http_requests_handler(context, match_object):
    extracted_count = match_object.group(1)
    extracted_count = int(extracted_count)

    context.extracted_http_requests.append(extracted_count)
