def num_formatter(val, chars, delta, left=False):
    align = '<' if left else ''
    return '{:{}{}d}'.format(int(val), align, chars)
