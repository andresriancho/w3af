# How many response results (success/fail) to store in order to calculate the
# xurllib error rate
MAX_RESPONSE_COLLECT = 100

# How many consecutive errors to receive before stopping the scan
MAX_ERROR_COUNT = 10

# There is a limit on MAX_ERROR_COUNT due to the way we use it in xurllib
assert MAX_RESPONSE_COLLECT > MAX_ERROR_COUNT * 2

# How many times to retry a request before we give up
MAX_HTTP_RETRIES = 2

