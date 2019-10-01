import re

from utils.utils import get_path
from utils.output import ListOutput, ListOutputItem

HTTP_METHOD_URL_RE = re.compile('\] (.*?) (.*?) (with data: ".*?" )?returned HTTP code')
HTTP_CODE_RE = re.compile('returned HTTP code "(.*?)"')
FROM_CACHE = 'from_cache=1'


def get_total_http_requests(scan_log_filename, scan):
    scan.seek(0)

    count = dict()
    methods = dict()
    urls = dict()
    cached_responses = 0.0

    for line in scan:

        if FROM_CACHE in line:
            cached_responses += 1

        if 'returned HTTP code' not in line:
            continue

        match = HTTP_CODE_RE.search(line)
        if match:
            code = match.group(1)

            if code in count:
                count[code] += 1
            else:
                count[code] = 1

        match = HTTP_METHOD_URL_RE.search(line)
        if match:
            method = match.group(1)
            url = match.group(2)

            if method in methods:
                methods[method] += 1
            else:
                methods[method] = 1

            url = get_path(url)

            if url in urls:
                urls[url] += 1
            else:
                urls[url] = 1

    total = sum(count.itervalues())

    output = ListOutput('http_requests')
    output.append(ListOutputItem('Total HTTP requests sent', total))

    if not total:
        return

    from_cache = '%.2f%%' % (cached_responses / total * 100,)
    output.append(ListOutputItem('HTTP responses from cache', from_cache))

    def by_value(a, b):
        return cmp(b[1], a[1])

    count_list = count.items()
    count_list.sort(by_value)

    responses_by_code = {}

    for code, num in count_list:
        responses_by_code[code] = (num, '%.2f%%' % (num / float(total) * 100,))

    output.append(ListOutputItem('HTTP responses by code',
                                 responses_by_code))

    methods_list = methods.items()
    methods_list.sort(by_value)

    requests_by_method = {}

    for method, count in methods_list:
        requests_by_method[method] = (count, '%.2f%%' % (count / float(total) * 100,))

    output.append(ListOutputItem('HTTP request method analysis',
                                 requests_by_method))

    urls_list = urls.items()
    urls_list.sort(by_value)
    urls_list = urls_list[:10]

    urls_with_more_requests = {}

    for url, num in urls_list:
        urls_with_more_requests[url] = (num, '%.2f%%' % (num / float(total) * 100,))

    output.append(ListOutputItem('URLs which received more HTTP requests',
                                 urls_with_more_requests))

    return output
