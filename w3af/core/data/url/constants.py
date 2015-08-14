# How many response results (success/fail) to store in order to calculate the
# xurllib error rate
MAX_RESPONSE_COLLECT = 100

# How many consecutive errors to receive before stopping the scan
MAX_ERROR_COUNT = 11

# There is a limit on MAX_ERROR_COUNT due to the way we use it in xurllib
assert MAX_RESPONSE_COLLECT > MAX_ERROR_COUNT * 2

# How many times to retry a request before we give up
MAX_HTTP_RETRIES = 2

#
# I've found some websites that check the user-agent string, and don't allow you
# to access if you don't have IE (mostly ASP.NET applications do this). So now
# we use the following user-agent string in w3af:
#
USER_AGENT = ('Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1;'
              ' Trident/4.0; w3af.org)')

# The error rate is multiplied by SOCKET_ERROR_DELAY to get the real delay time
# in seconds.
SOCKET_ERROR_DELAY = 0.15

# We want to pause on errors in order to allow the remote end to recover if
# we're flooding it, but some errors are allowed
ACCEPTABLE_ERROR_RATE = 5

# We want to pause on errors in order to allow the remote end to recover, but
# the stats analysis only makes sense once every N requests:
ERROR_DELAY_LIMIT = 5

# When we start scanning a site and w3af is configured to use auto-adjustable
# timeouts we actually need *some* timeout to start from, this is the value:
DEFAULT_TIMEOUT = 6

# Run the timeout adjustment every N HTTP requests
TIMEOUT_ADJUST_LIMIT = 50

# Used to calculate the timeout based on the average response time from the
# remote site. timeout = average_response_time * TIMEOUT_MULT_CONST
# https://github.com/andresriancho/w3af/issues/8698
TIMEOUT_MULT_CONST = 7.5

# In some cases the remote server is really quick to respond and we would be
# able to set timeouts as low as 0.01 seconds, while this is awesome it also
# means that any "small" load on our scanner and/or the server side will trigger
# a timeout.
#
# Another case where low timeouts might affect us is when the last responses
# used to calculate the timeout were all taken from a cache and the requests
# that we want to send require "expensive" SQL queries. This should be taken
# care by TIMEOUT_MULT_CONST but in some cases that's not enough.
#
# Thus I've decided to set a MIN timeout:
TIMEOUT_MIN = 0.35
