class dotdict(dict):
    """
    dot.notation access to dictionary attributes
    """
    __setattr__ = dict.__setitem__
    __getattr__ = dict.get
    __delattr__ = dict.__delitem__
