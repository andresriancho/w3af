#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import cookielib
import re
import socket
import sys
import urllib
import urllib2
import ConfigParser

from operator import itemgetter

TIMEOUT = 10
CONFIG_FILE = 'sqlharvest.cfg'
TABLES_FILE = 'tables.txt'
USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; AskTB5.3)'
SEARCH_URL = 'http://www.google.com/m?source=mobileproducts&dc=gorganic'
MAX_FILE_SIZE = 2 * 1024 * 1024  # if a result (.sql) file for downloading is more than 2MB in size just skip it
QUERY = 'CREATE TABLE ext:sql'
REGEX_URLS = r';u=([^"]+?)&amp;q='
REGEX_RESULT = r'(?i)CREATE TABLE\s*(/\*.*\*/)?\s*(IF NOT EXISTS)?\s*(?P<result>[^\(;]+)'

def main():
    tables = dict()
    cookies = cookielib.CookieJar()
    cookie_processor = urllib2.HTTPCookieProcessor(cookies)
    opener = urllib2.build_opener(cookie_processor)
    opener.addheaders = [("User-Agent", USER_AGENT)]

    conn = opener.open(SEARCH_URL)
    page = conn.read()  # set initial cookie values

    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)

    if not config.has_section("options"):
        config.add_section("options")
    if not config.has_option("options", "index"):
        config.set("options", "index", "0")

    i = int(config.get("options", "index"))

    try:
        with open(TABLES_FILE, 'r') as f:
            for line in f.xreadlines():
                if len(line) > 0 and ',' in line:
                    temp = line.split(',')
                    tables[temp[0]] = int(temp[1])
    except:
        pass

    socket.setdefaulttimeout(TIMEOUT)

    files, old_files = None, None
    try:
        while True:
            abort = False
            old_files = files
            files = []

            try:
                conn = opener.open("%s&q=%s&start=%d&sa=N" % (SEARCH_URL, QUERY.replace(' ', '+'), i * 10))
                page = conn.read()
                for match in re.finditer(REGEX_URLS, page):
                    files.append(urllib.unquote(match.group(1)))
                    if len(files) >= 10:
                        break
                abort = (files == old_files)

            except KeyboardInterrupt:
                raise

            except Exception, msg:
                print msg

            if abort:
                break

            sys.stdout.write("\n---------------\n")
            sys.stdout.write("Result page #%d\n" % (i + 1))
            sys.stdout.write("---------------\n")

            for sqlfile in files:
                print sqlfile

                try:
                    req = urllib2.Request(sqlfile)
                    response = urllib2.urlopen(req)

                    if "Content-Length" in response.headers:
                        if int(response.headers.get("Content-Length")) > MAX_FILE_SIZE:
                            continue

                    page = response.read()
                    found = False
                    counter = 0

                    for match in re.finditer(REGEX_RESULT, page):
                        counter += 1
                        table = match.group("result").strip().strip("`\"'").replace('"."', ".").replace("].[", ".").strip('[]')

                        if table and not any(_ in table for _ in ('>', '<', '--', ' ')):
                            found = True
                            sys.stdout.write('*')

                            if table in tables:
                                tables[table] += 1
                            else:
                                tables[table] = 1
                    if found:
                        sys.stdout.write("\n")

                except KeyboardInterrupt:
                    raise

                except Exception, msg:
                    print msg

            else:
                i += 1

    except KeyboardInterrupt:
        pass

    finally:
        with open(TABLES_FILE, 'w+') as f:
            tables = sorted(tables.items(), key=itemgetter(1), reverse=True)
            for table, count in tables:
                f.write("%s,%d\n" % (table, count))

        config.set("options", "index", str(i + 1))
        with open(CONFIG_FILE, 'w+') as f:
            config.write(f)

if __name__ == "__main__":
    main()
