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
TIMEOUT_MULT_CONST = 6.5

#
# I've found some websites that check the user-agent string, and don't allow you
# to access if you don't have IE (mostly ASP.NET applications do this). So now
# we use the following user-agent string in w3af:
#
USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1;'\
             ' Trident/4.0; w3af.org)'

# The error rate is multiplied by SOCKET_ERROR_DELAY to get the real delay time
# in seconds.
SOCKET_ERROR_DELAY = 0.15

# When we start scanning a site and w3af is configured to use auto-adjustable
# timeouts we actually need *some* timeout to start from, this is the value:
DEFAULT_TIMEOUT = 6

# Run the timeout adjustment every N HTTP requests
ADJUST_LIMIT = 25
