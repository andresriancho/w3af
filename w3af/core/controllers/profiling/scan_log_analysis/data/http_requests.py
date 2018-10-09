import re

from utils.utils import get_path

HTTP_METHOD_URL_RE = re.compile('\] (.*?) (.*?) (with data: ".*?" )?returned HTTP code')
HTTP_CODE_RE = re.compile('returned HTTP code "(.*?)"')
FROM_CACHE = 'from_cache=1'


def show_total_http_requests(scan):
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
    print('The scan sent %s HTTP requests' % total)

    if not total:
        return

    print('    %i%% responses came from HTTP cache' % (cached_responses / total * 100,))
    print('')

    def by_value(a, b):
        return cmp(b[1], a[1])

    count_list = count.items()
    count_list.sort(by_value)

    for code, num in count_list:
        args = (code, num, num / float(total) * 100)
        print('    HTTP response code %s was received %s times (%i%%)' % args)

    print('')

    methods_list = methods.items()
    methods_list.sort(by_value)

    for method, count in methods_list:
        args = (method, count, count / float(total) * 100)
        print('    HTTP method %s was sent %s times (%i%%)' % args)

    print('')

    urls_list = urls.items()
    urls_list.sort(by_value)
    urls_list = urls_list[:10]

    for url, num in urls_list:
        args = (url, num, num / float(total) * 100)
        print('    URL %s received %s requests (%i%%)' % args)

    print('')
