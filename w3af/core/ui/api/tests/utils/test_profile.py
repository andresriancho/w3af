"""
test_profile.py

Copyright 2015 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
from nose.tools import nottest
from w3af.core.controllers.ci.moth import get_moth_http

PROFILE_URL = 'http://127.0.0.1:8000/audit/sql_injection/'

FAST_TEST_PROFILE = """[profile]
description = sqli
name = sqli

[crawl.web_spider]
only_forward = True
follow_regex = .*
ignore_regex =

[audit.sqli]

[output.console]
verbose = True

[target]
target = http://127.0.0.1:8000/audit/sql_injection/

[misc-settings]
fuzz_cookies = False
fuzz_form_files = True
fuzz_url_filenames = False
fuzz_url_parts = False
fuzzed_files_extension = gif
fuzzable_headers =
form_fuzzing_mode = tmb
stop_on_first_exception = False
max_discovery_time = 120
interface = wlan1
local_ip_address = 10.1.2.24
non_targets =
msf_location = /opt/metasploit3/bin/

[http-settings]
timeout = 0
headers_file =
basic_auth_user =
basic_auth_passwd =
basic_auth_domain =
ntlm_auth_domain =
ntlm_auth_user =
ntlm_auth_passwd =
ntlm_auth_url =
cookie_jar_file =
ignore_session_cookies = False
proxy_port = 8080
proxy_address =
user_agent = w3af.org
rand_user_agent = False
max_file_size = 400000
max_http_retries = 2
max_requests_per_second = 0
always_404 =
never_404 =
string_match_404 =
url_parameter =

"""


SLOW_TEST_PROFILE = """[profile]
description = slow
name = slow

[crawl.web_spider]
only_forward = True
follow_regex = .*
ignore_regex =

[audit.sqli]

[audit.xss]

[audit.os_commanding]

[output.console]
verbose = True

[target]
target = http://127.0.0.1:8000/audit/sql_injection/

[misc-settings]
fuzz_cookies = False
fuzz_form_files = True
fuzz_url_filenames = False
fuzz_url_parts = False
fuzzed_files_extension = gif
fuzzable_headers =
form_fuzzing_mode = tmb
stop_on_first_exception = False
max_discovery_time = 120
interface = wlan1
local_ip_address = 10.1.2.24
non_targets =
msf_location = /opt/metasploit3/bin/

[http-settings]
timeout = 0
headers_file =
basic_auth_user =
basic_auth_passwd =
basic_auth_domain =
ntlm_auth_domain =
ntlm_auth_user =
ntlm_auth_passwd =
ntlm_auth_url =
cookie_jar_file =
ignore_session_cookies = False
proxy_port = 8080
proxy_address =
user_agent = w3af.org
rand_user_agent = False
max_file_size = 400000
max_http_retries = 2
max_requests_per_second = 0
always_404 =
never_404 =
string_match_404 =
url_parameter =

"""


@nottest
def get_test_profile(profile=FAST_TEST_PROFILE):
    moth = get_moth_http('/')

    target_url = PROFILE_URL.replace('http://127.0.0.1:8000/', moth)
    profile = profile.replace('http://127.0.0.1:8000/', moth)

    return profile, target_url


def get_expected_vuln_names():
    return ['SQL injection'] * 4


def get_expected_vuln_urls(target_url):
    return [u'%swhere_integer_qs.py' % target_url,
            u'%swhere_string_single_qs.py' % target_url,
            u'%swhere_integer_form.py' % target_url]
