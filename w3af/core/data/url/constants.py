# How many response results (success/fail) to store in order to calculate the
# xurllib error rate
MAX_RESPONSE_COLLECT = 100

# How many consecutive errors to receive before stopping the scan
MAX_ERROR_COUNT = 11

# There is a limit on MAX_ERROR_COUNT due to the way we use it in xurllib
assert MAX_RESPONSE_COLLECT > MAX_ERROR_COUNT * 2

# How many times to retry a request before we give up
MAX_HTTP_RETRIES = 2

# Used to calculate the timeout based on the average response time from the
# remote site. timeout = average_response_time * TIMEOUT_MULT_CONST
# https://github.com/andresriancho/w3af/issues/8698
TIMEOUT_MULT_CONST = 10

