"""
test_ruby_export.py

Copyright 2012 Andres Riancho

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
import unittest

from w3af.core.data.export.ruby_export import ruby_export

EXPECTED_SIMPLE = """require 'net/https'

url = URI.parse("http://www.w3af.org/")
data = nil
headers = {
    "Host" => "www.w3af.org",
    "Foo" => "bar"
}
res = Net::HTTP.start(url.host, url.port) do |http|
    http.use_ssl = false
    http.send_request("GET", url.path, data, headers)
end

puts res.body
"""

EXPECTED_POST = """require 'net/https'

url = URI.parse("http://www.w3af.org/")
data = "a=1"
headers = {
    "Host" => "www.w3af.org",
    "Content-Type" => "application/x-www-form-urlencoded"
}
res = Net::HTTP.start(url.host, url.port) do |http|
    http.use_ssl = false
    http.send_request("POST", url.path, data, headers)
end

puts res.body
"""

EXPECTED_POST_REPEATED = """require 'net/https'

url = URI.parse("http://www.w3af.org/")
data = "a=1&a=2"
headers = {
    "Host" => "www.w3af.org",
    "Content-Type" => "application/x-www-form-urlencoded",
    "Foo" => "spam, eggs"
}
res = Net::HTTP.start(url.host, url.port) do |http|
    http.use_ssl = false
    http.send_request("POST", url.path, data, headers)
end

puts res.body
"""


class TestRubyExport(unittest.TestCase):

    def test_export_GET(self):
        http_request = 'GET http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Foo: bar\n' \
                       '\n'
        ruby_code = ruby_export(http_request)
        self.assertEquals(ruby_code, EXPECTED_SIMPLE)

    def test_export_POST(self):
        http_request = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 3\n' \
                       'Content-Type: application/x-www-form-urlencoded\n' \
                       '\n' \
                       'a=1'
        ruby_code = ruby_export(http_request)
        self.assertEquals(ruby_code, EXPECTED_POST)

    def test_export_POST_repeated(self):
        http_request = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 7\n' \
                       'Content-Type: application/x-www-form-urlencoded\n' \
                       'Foo: spam\n' \
                       'Foo: eggs\n' \
                       '\n' \
                       'a=1&a=2'
        ruby_code = ruby_export(http_request)
        self.assertEquals(ruby_code, EXPECTED_POST_REPEATED)

    def test_export_inject(self):
        http_request = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 7\n' \
                       'Content-Type: application/x-www-form-urlencoded\n' \
                       'Foo: sp"am\n' \
                       'Foo: eggs\n' \
                       '\n' \
                       'a=1&a=2"3'
        ruby_code = ruby_export(http_request)
        self.assertIn('a=1&a=2%223', ruby_code)
        self.assertIn("sp\\\"am", ruby_code)
