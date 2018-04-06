def median(numbers):
    numbers = sorted(numbers)
    center = len(numbers) / 2
    if len(numbers) % 2 == 0:
        return sum(numbers[center - 1:center + 1]) / 2.0
    else:
        return numbers[center]


def mean(data):
    """
    Return the sample arithmetic mean of data.
    """
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return sum(data) / float(n)


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


def outliers_modified_z_score(ys):
    threshold = 7.5

    median_y = median(ys)
    median_absolute_deviation_y = median([abs(y - median_y) for y in ys])

    # This is to avoid an ugly division by zero error
    if median_absolute_deviation_y == 0:
        median_absolute_deviation_y = 0.0001

    modified_z_scores = [0.6745 * (y - median_y) / median_absolute_deviation_y for y in ys]

    result = []

    for idx, modified_z_score in enumerate(modified_z_scores):
        if abs(modified_z_score) > threshold:
            result.append(None)
        else:
            result.append(ys[idx])

    return result
