def mean(data):
    """
    Return the sample arithmetic mean of data.
    """
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return sum(data)/float(n)


def _ss(data):
    """
    Return sum of square deviations of sequence data.
    """
    c = mean(data)
    ss = sum((x-c)**2 for x in data)
    return ss


def stddev(data, ddof=0):
    """
    Calculates the population standard deviation
    by default; specify ddof=1 to compute the sample
    standard deviation.
    """
    n = len(data)
    if n < 2:
        raise ValueError('variance requires at least two data points')
    ss = _ss(data)
    pvar = ss / (n-ddof)
    return pvar ** 0.5


def drop_outliers(data_points, offset=1.0):
    _mean = mean(data_points)
    _std_dev = stddev(data_points)

    def _drop_outliers(i):
        if abs(i - _mean) <= _std_dev * offset:
            return i

    return filter(_drop_outliers, data_points)
