import re
import json

from utils.output import ListOutput, ListOutputItem
from utils.dotdict import dotdict


CRAWL_TIME_BY_STRATEGY = re.compile('Spent (.*?) seconds in crawl strategy (.*?) for (.*?) \(did:')

EVENT_IGNORE = re.compile('Ignoring "(.*?)" event on selector "(.*?)" and URL "(.*?)"')
EVENT_DISPATCH_STATS = re.compile(r'Event dispatch error count is (.*?). Already processed (.*?) events with types: (.*?)\. \(did:')

EXTRACTED_HTTP_REQUESTS = re.compile(r'Extracted (.*?) new HTTP requests from (.*?)')
TOTAL_CHROME_PROXY_REQUESTS = re.compile(r'A total of (.*?) HTTP requests have been read by the web_spider')

SECONDS_LOADING_URL = re.compile(r'Spent (.*?) seconds loading URL (.*?) in chrome')
WAIT_FOR_LOAD_TIMEOUTS = re.compile(r'wait_for_load\(timeout=(.*?)\) timed out')

CHROME_POOL_PERF = re.compile(r'ChromePool.get\(\) took (.*?) seconds to create an instance')
WEBSOCKET_MESSAGE_WAIT_TIME = re.compile(r'Waited (.*?) seconds for message with ID')
CHROME_CRAWLER_STATUS = re.compile(r'ChromeCrawler status \((.*?) running tasks, (.*?) workers, (.*?) tasks in queue\)')

REGEX_NAMES = {
    'CRAWL_TIME_BY_STRATEGY',

    'EVENT_IGNORE',
    'EVENT_DISPATCH_STATS',

    'EXTRACTED_HTTP_REQUESTS',
    'TOTAL_CHROME_PROXY_REQUESTS',

    'SECONDS_LOADING_URL',
    'WAIT_FOR_LOAD_TIMEOUTS',

    'CHROME_POOL_PERF',
    'WEBSOCKET_MESSAGE_WAIT_TIME',
    'CHROME_CRAWLER_STATUS'
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
    context.total_chrome_proxy_requests = list()

    context.seconds_loading_url = list()
    context.wait_for_load_timeouts = list()

    context.chrome_pool_perf = list()
    context.websocket_message_wait_time = list()
    context.chrome_crawler_status = list()

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
    post_process_seconds_loading_url(context, output)
    post_process_total_chrome_proxy_requests(context, output)
    post_process_wait_for_load_timeouts(context, output)
    post_process_chrome_pool_perf(context, output)
    post_process_websocket_message_wait_time(context, output)
    post_process_chrome_crawler_status(context, output)


def post_process_chrome_crawler_status(context, output):
    all_running_tasks = []
    all_pool_workers = []
    all_queued_tasks = []

    for running_tasks, pool_workers, queued_tasks in context.chrome_crawler_status:
        all_running_tasks.append(running_tasks)
        all_pool_workers.append(pool_workers)
        all_queued_tasks.append(queued_tasks)

    average_running_tasks = 'n/a'

    if len(all_running_tasks):
        average_running_tasks = round(sum(all_running_tasks) / len(all_running_tasks), 2)

    average_queued_tasks = 'n/a'

    if len(all_queued_tasks):
        average_queued_tasks = round(sum(all_queued_tasks) / len(all_queued_tasks), 2)

    data = {'Pool worker sizes during scan': ', '.join(str(i) for i in set(all_pool_workers)),
            'Max running tasks': max(all_running_tasks),
            'Avg running tasks': average_running_tasks,
            'Max queued tasks': max(all_queued_tasks),
            'Avg queued tasks': average_queued_tasks}
    output.append(ListOutputItem('Chrome crawler status', data))


def post_process_websocket_message_wait_time(context, output):
    total_seconds_waiting_for_message = sum(context.websocket_message_wait_time)

    max_seconds_waiting = context.websocket_message_wait_time[:]
    max_seconds_waiting.sort()
    max_seconds_waiting.reverse()
    max_seconds_waiting = max_seconds_waiting[:10]

    average = 'n/a'

    if len(context.chrome_pool_perf):
        average = round(total_seconds_waiting_for_message / len(context.websocket_message_wait_time), 2)

    data = {'Total waited time': total_seconds_waiting_for_message,
            'Top 10 larger wait times': max_seconds_waiting,
            'Average wait time': average,
            'Number of messages': len(context.websocket_message_wait_time)}
    output.append(ListOutputItem('Time waiting for chrome websocket messages (seconds)', data))


def post_process_chrome_pool_perf(context, output):
    total_seconds_waiting_for_chrome_inst = sum(context.chrome_pool_perf)

    max_seconds_waiting = context.chrome_pool_perf[:]
    max_seconds_waiting.sort()
    max_seconds_waiting.reverse()
    max_seconds_waiting = max_seconds_waiting[:10]

    average = 'n/a'

    if len(context.chrome_pool_perf):
        average = round(total_seconds_waiting_for_chrome_inst / len(context.chrome_pool_perf), 2)

    data = {'Total waited time': total_seconds_waiting_for_chrome_inst,
            'Top 10 larger wait times': max_seconds_waiting,
            'Average wait time': average,
            'Number of chrome instances': len(context.chrome_pool_perf)}
    output.append(ListOutputItem('Time waiting for chrome instance from pool (seconds)', data))


def post_process_total_chrome_proxy_requests(context, output):
    total_chrome_requests = context.total_chrome_proxy_requests[-1]

    data = {'Total': total_chrome_requests}
    output.append(ListOutputItem('HTTP requests sent by chrome', data))


def post_process_seconds_loading_url(context, output):
    total_seconds_loading_url = 0

    for spent, url in context.seconds_loading_url:
        total_seconds_loading_url += spent

    total_seconds_loading_url = round(total_seconds_loading_url, 2)

    max_by_url = context.seconds_loading_url[:]
    max_by_url.sort(sort_by_first)
    max_by_url.reverse()
    max_by_url = max_by_url[:10]

    average = 'n/a'

    if len(context.seconds_loading_url):
        average = round(total_seconds_loading_url / len(context.seconds_loading_url), 2)

    data = {'Total': total_seconds_loading_url,
            'Top 10 most time consuming by URL': max_by_url,
            'Average': average,
            'Number of loaded URLs': len(context.seconds_loading_url)}
    output.append(ListOutputItem('Time loading URL (seconds)', data))


def post_process_extracted_http_requests(context, output):
    max_extracted_http_requests = max(context.extracted_http_requests)
    min_extracted_http_requests = min(context.extracted_http_requests)

    avg_extracted_http_requests = 0

    if len(context.extracted_http_requests):
        avg_extracted_http_requests = sum(context.extracted_http_requests) / len(context.extracted_http_requests)

    data = {'max': max_extracted_http_requests,
            'min': min_extracted_http_requests,
            'avg': avg_extracted_http_requests}

    output.append(ListOutputItem('Extracted HTTP requests per page', data))


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

    average = 'n/a'

    if len(context.js_crawl_strategy_times):
        average = round(crawl_time_js_total / len(context.js_crawl_strategy_times), 2)

    data = {'Total': crawl_time_js_total,
            'Top 10 most time consuming by URL': js_max_by_url,
            'Average': average,
            'Number of calls to strategy': len(context.js_crawl_strategy_times)}
    output.append(ListOutputItem('JS crawl times (seconds)', data))

    average = 'n/a'

    if len(context.dom_dump_crawl_strategy_times):
        average = round(crawl_time_dom_total / len(context.dom_dump_crawl_strategy_times), 2)

    data = {'Total': crawl_time_dom_total,
            'Top 10 most time consuming by URL': dom_dump_max_by_url,
            'Average': average,
            'Number of calls to strategy': len(context.dom_dump_crawl_strategy_times)}
    output.append(ListOutputItem('DOM dump crawl times (seconds)', data))


def post_process_wait_for_load_timeouts(context, output):
    total_page_load_fail = len(context.wait_for_load_timeouts)

    data = {'Total': total_page_load_fail,
            'Timeout setting (seconds)': 'n/a' if not context.wait_for_load_timeouts else context.wait_for_load_timeouts[0]}
    output.append(ListOutputItem('Page load timeout reached', data))


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


def wait_for_load_timeouts_handler(context, match_object):
    seconds = match_object.group(1)
    seconds = float(seconds)

    context.wait_for_load_timeouts.append(seconds)


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


def seconds_loading_url_handler(context, match_object):
    seconds = match_object.group(1)
    seconds = float(seconds)

    url = match_object.group(2)

    context.seconds_loading_url.append((seconds, url))


def total_chrome_proxy_requests_handler(context, match_object):
    total = match_object.group(1)
    total = int(total)

    context.total_chrome_proxy_requests.append(total)


def chrome_pool_perf_handler(context, match_object):
    seconds = match_object.group(1)
    seconds = float(seconds)

    context.chrome_pool_perf.append(seconds)


def websocket_message_wait_time_handler(context, match_object):
    seconds = match_object.group(1)
    seconds = float(seconds)

    context.websocket_message_wait_time.append(seconds)


def chrome_crawler_status_handler(context, match_object):
    running_tasks = match_object.group(1)
    pool_workers = match_object.group(2)
    queued_tasks = match_object.group(3)

    running_tasks = int(running_tasks)
    pool_workers = int(pool_workers)
    queued_tasks = int(queued_tasks)

    context.chrome_crawler_status.append((running_tasks, pool_workers, queued_tasks))
