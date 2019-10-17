#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import codecs
import gzip
import logging
import re
import StringIO
import struct
import zlib

from lib.core.common import Backend
from lib.core.common import extractErrorMessage
from lib.core.common import extractRegexResult
from lib.core.common import getPublicTypeMembers
from lib.core.common import getUnicode
from lib.core.common import randomStr
from lib.core.common import readInput
from lib.core.common import resetCookieJar
from lib.core.common import singleTimeLogMessage
from lib.core.common import singleTimeWarnMessage
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.decorators import cachedmethod
from lib.core.enums import DBMS
from lib.core.enums import HTTP_HEADER
from lib.core.enums import PLACE
from lib.core.exception import SqlmapCompressionException
from lib.core.settings import BLOCKED_IP_REGEX
from lib.core.settings import DEFAULT_COOKIE_DELIMITER
from lib.core.settings import DEV_EMAIL_ADDRESS
from lib.core.settings import EVENTVALIDATION_REGEX
from lib.core.settings import MAX_CONNECTION_TOTAL_SIZE
from lib.core.settings import META_CHARSET_REGEX
from lib.core.settings import PARSE_HEADERS_LIMIT
from lib.core.settings import SELECT_FROM_TABLE_REGEX
from lib.core.settings import UNICODE_ENCODING
from lib.core.settings import VIEWSTATE_REGEX
from lib.parse.headers import headersParser
from lib.parse.html import htmlParser
from lib.utils.htmlentities import htmlEntities
from thirdparty.chardet import detect
from thirdparty.odict.odict import OrderedDict


def forgeHeaders(items=None, base=None):
    """
    Prepare HTTP Cookie, HTTP User-Agent and HTTP Referer headers to use when performing
    the HTTP requests
    """

    items = items or {}

    for _ in items.keys():
        if items[_] is None:
            del items[_]

    headers = OrderedDict(base or conf.httpHeaders)
    headers.update(items.items())

    class _str(str):
        def capitalize(self):
            return _str(self)

        def title(self):
            return _str(self)

    _ = headers
    headers = OrderedDict()
    for key, value in _.items():
        success = False

        for _ in headers:
            if _.upper() == key.upper():
                del headers[_]
                break

        if key.upper() not in (_.upper()
                               for _ in getPublicTypeMembers(HTTP_HEADER, True)):
            try:
                # dirty hack for http://bugs.python.org/issue12455
                headers[_str(key)] = value
            # don't do the hack on non-ASCII header names (they have to be
            # properly encoded later on)
            except UnicodeEncodeError:
                pass
            else:
                success = True
        if not success:
            key = '-'.join(_.capitalize() for _ in key.split('-'))
            headers[key] = value

    if conf.cj:
        if HTTP_HEADER.COOKIE in headers:
            for cookie in conf.cj:
                if cookie.domain_specified and not (
                        conf.hostname or "").endswith(
                        cookie.domain):
                    continue

                if ("%s=" % getUnicode(cookie.name)) in getUnicode(
                        headers[HTTP_HEADER.COOKIE]):
                    if conf.loadCookies:
                        conf.httpHeaders = filter(
                            None,
                            ((item if item[0] != HTTP_HEADER.COOKIE else None) for item in conf.httpHeaders))
                    elif kb.mergeCookies is None:
                        message = "you provided a HTTP %s header value. " % HTTP_HEADER.COOKIE
                        message += "The target URL provided its own cookies within "
                        message += "the HTTP %s header which intersect with yours. " % HTTP_HEADER.SET_COOKIE
                        message += "Do you want to merge them in further requests? [Y/n] "

                        kb.mergeCookies = readInput(
                            message, default='Y', boolean=True)

                    if kb.mergeCookies and kb.injection.place != PLACE.COOKIE:
                        def _(x): return re.sub(
                            r"(?i)\b%s=[^%s]+" %
                            (re.escape(
                                getUnicode(
                                    cookie.name)), conf.cookieDel or DEFAULT_COOKIE_DELIMITER), ("%s=%s" %
                                                                                                 (getUnicode(
                                                                                                     cookie.name), getUnicode(
                                                                                                     cookie.value))).replace(
                                '\\', r'\\'), x)
                        headers[HTTP_HEADER.COOKIE] = _(
                            headers[HTTP_HEADER.COOKIE])

                        if PLACE.COOKIE in conf.parameters:
                            conf.parameters[PLACE.COOKIE] = _(
                                conf.parameters[PLACE.COOKIE])

                        conf.httpHeaders = [
                            (item[0], item[1] if item[0] != HTTP_HEADER.COOKIE else _(
                                item[1])) for item in conf.httpHeaders]

                elif not kb.testMode:
                    headers[HTTP_HEADER.COOKIE] += "%s %s=%s" % (
                        conf.cookieDel or DEFAULT_COOKIE_DELIMITER, getUnicode(cookie.name), getUnicode(cookie.value))

        if kb.testMode and not any((conf.csrfToken, conf.safeUrl)):
            resetCookieJar(conf.cj)

    return headers


def parseResponse(page, headers, status=None):
    """
    @param page: the page to parse to feed the knowledge base htmlFp
    (back-end DBMS fingerprint based upon DBMS error messages return
    through the web application) list and absFilePaths (absolute file
    paths) set.
    """

    if headers:
        headersParser(headers)

    if page:
        htmlParser(page if not status else "%s\n\n%s" % (status, page))


@cachedmethod
def checkCharEncoding(encoding, warn=True):
    """
    Checks encoding name, repairs common misspellings and adjusts to
    proper namings used in codecs module

    >>> checkCharEncoding('iso-8858', False)
    'iso8859-1'
    >>> checkCharEncoding('en_us', False)
    'utf8'
    """

    if encoding:
        encoding = encoding.lower()
    else:
        return encoding

    # Reference: http://www.destructor.de/charsets/index.htm
    translate = {
        "windows-874": "iso-8859-11",
        "utf-8859-1": "utf8",
        "en_us": "utf8",
        "macintosh": "iso-8859-1",
        "euc_tw": "big5_tw",
        "th": "tis-620",
        "unicode": "utf8",
        "utc8": "utf8",
        "ebcdic": "ebcdic-cp-be",
        "iso-8859": "iso8859-1",
        "iso-8859-0": "iso8859-1",
        "ansi": "ascii",
        "gbk2312": "gbk",
        "windows-31j": "cp932",
        "en": "us"}

    for delimiter in (';', ',', '('):
        if delimiter in encoding:
            encoding = encoding[:encoding.find(delimiter)].strip()

    encoding = encoding.replace("&quot", "")

    # popular typos/errors
    if "8858" in encoding:
        encoding = encoding.replace("8858", "8859")  # iso-8858 -> iso-8859
    elif "8559" in encoding:
        encoding = encoding.replace("8559", "8859")  # iso-8559 -> iso-8859
    elif "8895" in encoding:
        encoding = encoding.replace("8895", "8859")  # iso-8895 -> iso-8859
    elif "5889" in encoding:
        encoding = encoding.replace("5889", "8859")  # iso-5889 -> iso-8859
    elif "5589" in encoding:
        encoding = encoding.replace("5589", "8859")  # iso-5589 -> iso-8859
    elif "2313" in encoding:
        encoding = encoding.replace("2313", "2312")  # gb2313 -> gb2312
    elif encoding.startswith("x-"):
        # x-euc-kr -> euc-kr  /  x-mac-turkish -> mac-turkish
        encoding = encoding[len("x-"):]
    elif "windows-cp" in encoding:
        # windows-cp-1254 -> windows-1254
        encoding = encoding.replace("windows-cp", "windows")

    # name adjustment for compatibility
    if encoding.startswith("8859"):
        encoding = "iso-%s" % encoding
    elif encoding.startswith("cp-"):
        encoding = "cp%s" % encoding[3:]
    elif encoding.startswith("euc-"):
        encoding = "euc_%s" % encoding[4:]
    elif encoding.startswith("windows") and not encoding.startswith("windows-"):
        encoding = "windows-%s" % encoding[7:]
    elif encoding.find("iso-88") > 0:
        encoding = encoding[encoding.find("iso-88"):]
    elif encoding.startswith("is0-"):
        encoding = "iso%s" % encoding[4:]
    elif encoding.find("ascii") > 0:
        encoding = "ascii"
    elif encoding.find("utf8") > 0:
        encoding = "utf8"
    elif encoding.find("utf-8") > 0:
        encoding = "utf-8"

    # Reference: http://philip.html5.org/data/charsets-2.html
    if encoding in translate:
        encoding = translate[encoding]
    elif encoding in ("null", "{charset}", "charset", "*") or not re.search(r"\w", encoding):
        return None

    # Reference: http://www.iana.org/assignments/character-sets
    # Reference: http://docs.python.org/library/codecs.html
    try:
        codecs.lookup(
            encoding.encode(UNICODE_ENCODING) if isinstance(
                encoding, unicode) else encoding)
    except (LookupError, ValueError):
        if warn:
            warnMsg = "unknown web page charset '%s'. " % encoding
            warnMsg += "Please report by e-mail to '%s'" % DEV_EMAIL_ADDRESS
            singleTimeLogMessage(warnMsg, logging.WARN, encoding)
        encoding = None

    if encoding:
        try:
            unicode(randomStr(), encoding)
        except BaseException:
            if warn:
                warnMsg = "invalid web page charset '%s'" % encoding
                singleTimeLogMessage(warnMsg, logging.WARN, encoding)
            encoding = None

    return encoding


def getHeuristicCharEncoding(page):
    """
    Returns page encoding charset detected by usage of heuristics
    Reference: http://chardet.feedparser.org/docs/
    """

    key = hash(page)
    retVal = kb.cache.encoding.get(key) or detect(page)["encoding"]
    kb.cache.encoding[key] = retVal

    if retVal:
        infoMsg = "heuristics detected web page charset '%s'" % retVal
        singleTimeLogMessage(infoMsg, logging.INFO, retVal)

    return retVal


def decodePage(page, contentEncoding, contentType):
    """
    Decode compressed/charset HTTP response
    """

    if not page or (conf.nullConnection and len(page) < 2):
        return getUnicode(page)

    if isinstance(contentEncoding, basestring) and contentEncoding:
        contentEncoding = contentEncoding.lower()
    else:
        contentEncoding = ""

    if isinstance(contentType, basestring) and contentType:
        contentType = contentType.lower()
    else:
        contentType = ""

    if contentEncoding in ("gzip", "x-gzip", "deflate"):
        if not kb.pageCompress:
            return None

        try:
            if contentEncoding == "deflate":
                # Reference:
                # http://stackoverflow.com/questions/1089662/python-inflate-and-deflate-implementations
                data = StringIO.StringIO(zlib.decompress(page, -15))
            else:
                data = gzip.GzipFile("", "rb", 9, StringIO.StringIO(page))
                # Reference:
                # http://pydoc.org/get.cgi/usr/local/lib/python2.5/gzip.py
                size = struct.unpack("<l", page[-4:])[0]
                if size > MAX_CONNECTION_TOTAL_SIZE:
                    raise Exception("size too large")

            page = data.read()
        except Exception as msg:
            # in some cases, invalid "Content-Encoding" appears for plain HTML
            # (should be ignored)
            if "<html" not in page:
                errMsg = "detected invalid data for declared content "
                errMsg += "encoding '%s' ('%s')" % (contentEncoding, msg)
                singleTimeLogMessage(errMsg, logging.ERROR)

                warnMsg = "turning off page compression"
                singleTimeWarnMessage(warnMsg)

                kb.pageCompress = False
                raise SqlmapCompressionException

    if not conf.encoding:
        httpCharset, metaCharset = None, None

        # Reference:
        # http://stackoverflow.com/questions/1020892/python-urllib2-read-to-unicode
        if contentType.find("charset=") != -1:
            httpCharset = checkCharEncoding(contentType.split("charset=")[-1])

        metaCharset = checkCharEncoding(
            extractRegexResult(
                META_CHARSET_REGEX, page))

        if (any((httpCharset, metaCharset)) and not all((httpCharset, metaCharset)))\
                or (httpCharset == metaCharset and all((httpCharset, metaCharset))):
            # Reference:
            # http://bytes.com/topic/html-css/answers/154758-http-equiv-vs-true-header-has-precedence
            kb.pageEncoding = httpCharset or metaCharset
            debugMsg = "declared web page charset '%s'" % kb.pageEncoding
            singleTimeLogMessage(debugMsg, logging.DEBUG, debugMsg)
        else:
            kb.pageEncoding = None
    else:
        kb.pageEncoding = conf.encoding

    # can't do for all responses because we need to support binary files too
    if not isinstance(page, unicode) and "text/" in contentType:
        if kb.heuristicMode:
            kb.pageEncoding = kb.pageEncoding or checkCharEncoding(
                getHeuristicCharEncoding(page))
            page = getUnicode(page, kb.pageEncoding)
        else:
            # e.g. &#195;&#235;&#224;&#226;&#224;
            if "&#" in page:
                page = re.sub(r"&#(\d{1,3});", lambda _: chr(
                    int(_.group(1))) if int(_.group(1)) < 256 else _.group(0), page)

            # e.g. %20%28%29
            if "%" in page:
                page = re.sub(
                    r"%([0-9a-fA-F]{2})",
                    lambda _: _.group(1).decode("hex"),
                    page)

            # e.g. &amp;
            page = re.sub(r"&([^;]+);", lambda _: chr(htmlEntities[_.group(1)])
                          if htmlEntities.get(_.group(1), 256) < 256 else _.group(0), page)

            kb.pageEncoding = kb.pageEncoding or checkCharEncoding(
                getHeuristicCharEncoding(page))

            if kb.pageEncoding and kb.pageEncoding.lower() == "utf-8-sig":
                kb.pageEncoding = "utf-8"
                # Reference: https://docs.python.org/2/library/codecs.html
                # (Note: noticed problems when "utf-8-sig" is left to Python
                # for handling)
                if page and page.startswith("\xef\xbb\xbf"):
                    page = page[3:]

            page = getUnicode(page, kb.pageEncoding)

            # e.g. &#8217;&#8230;&#8482;
            if "&#" in page:
                def _(match):
                    retVal = match.group(0)
                    try:
                        retVal = unichr(int(match.group(1)))
                    except ValueError:
                        pass
                    return retVal
                page = re.sub(r"&#(\d+);", _, page)

            # e.g. &zeta;
            page = re.sub(r"&([^;]+);", lambda _: unichr(htmlEntities[_.group(1)])
                          if htmlEntities.get(_.group(1), 0) > 255 else _.group(0), page)

    return page


def processResponse(page, responseHeaders, status=None):
    kb.processResponseCounter += 1

    page = page or ""

    parseResponse(page, responseHeaders if kb.processResponseCounter <
                  PARSE_HEADERS_LIMIT else None, status)

    if not kb.tableFrom and Backend.getIdentifiedDbms() in (DBMS.ACCESS,):
        kb.tableFrom = extractRegexResult(SELECT_FROM_TABLE_REGEX, page)
    else:
        kb.tableFrom = None

    if conf.parseErrors:
        msg = extractErrorMessage(page)

        if msg:
            logger.warning("parsed DBMS error message: '%s'" % msg.rstrip('.'))

    if kb.originalPage is None:
        for regex in (EVENTVALIDATION_REGEX, VIEWSTATE_REGEX):
            match = re.search(regex, page)
            if match and PLACE.POST in conf.parameters:
                name, value = match.groups()
                if PLACE.POST in conf.paramDict and name in conf.paramDict[PLACE.POST]:
                    if conf.paramDict[PLACE.POST][name] in page:
                        continue
                    else:
                        msg = "do you want to automatically adjust the value of '%s'? [y/N]" % name

                        if not readInput(msg, default='N', boolean=True):
                            continue

                        conf.paramDict[PLACE.POST][name] = value
                conf.parameters[PLACE.POST] = re.sub(r"(?i)(%s=)[^&]+" % re.escape(
                    name), r"\g<1>%s" % re.escape(value), conf.parameters[PLACE.POST])

    if not kb.browserVerification and re.search(
            r"(?i)browser.?verification", page or ""):
        kb.browserVerification = True
        warnMsg = "potential browser verification protection mechanism detected"
        if re.search(r"(?i)CloudFlare", page):
            warnMsg += " (CloudFlare)"
        singleTimeWarnMessage(warnMsg)

    if not kb.captchaDetected and re.search(r"(?i)captcha", page or ""):
        for match in re.finditer(r"(?si)<form.+?</form>", page):
            if re.search(r"(?i)captcha", match.group(0)):
                kb.captchaDetected = True
                warnMsg = "potential CAPTCHA protection mechanism detected"
                if re.search(r"(?i)<title>[^<]*CloudFlare", page):
                    warnMsg += " (CloudFlare)"
                singleTimeWarnMessage(warnMsg)
                break

    if re.search(BLOCKED_IP_REGEX, page):
        warnMsg = "it appears that you have been blocked by the target server"
        singleTimeWarnMessage(warnMsg)
