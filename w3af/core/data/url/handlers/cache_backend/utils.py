import hashlib


def gen_hash(request):
    """
    Generate an unique ID for a request
    """
    req = request
    headers_1 = ''.join('%s%s' % (h, v) for h, v in req.headers.iteritems())
    headers_2 = ''.join('%s%s' % (h, v) for h, v in req.unredirected_hdrs.iteritems())
    
    the_str = '%s%s%s%s%s' % (req.get_method(),
                              req.get_full_url(),
                              headers_1,
                              headers_2,
                              req.get_data() or '')

    # Commented out the encode call to fix #1917
    # https://github.com/andresriancho/w3af/issues/1917
    #
    # But, as with everything else related with encoding, I'm unsure and that's
    # why I won't remove the line for some time.
    #
    #the_str = the_str.encode('utf-8', 'ignore')

    return hashlib.md5(the_str).hexdigest()
