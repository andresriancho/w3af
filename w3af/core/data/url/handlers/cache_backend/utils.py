import hashlib


def gen_hash(request):
    """
    Generate an unique ID for a request
    """
    req = request
    headers_1 = ''.join('%s%s' % (h, v) for h, v in req.headers.iteritems())
    headers_2 = ''.join('%s%s' % (h, v) for h, v in req.unredirected_hdrs.iteritems())
    
    the_str = '%s%s%s%s%s' % (
                             req.get_method(),
                             req.get_full_url(),
                             headers_1,
                             headers_2,
                             req.get_data() or ''
                             )
    
    the_str = the_str.encode('utf-8', 'ignore')
    return hashlib.md5(the_str).hexdigest()
