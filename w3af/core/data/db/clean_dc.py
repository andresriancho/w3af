"""
clean_dc.py

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
from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.misc.encoding import smart_str_ignore

FILENAME_TOKEN = 'file-5692fef3f5dcd97'
PATH_TOKEN = 'path-0fb923a04c358a37c'


def clean_data_container(data_container):
    """
    A simplified/serialized version of the data container. Every data
    container is serialized to query string format, but we don't lose info
    since we just want to keep the keys and value types.

    This simplification allows us to store and compare complex data
    containers which might have unique ids (such as multipart).

    We replace the value by a number/string depending on the content, this
    allows us to quickly search and match two URLs which are similar
    """
    result = []

    for key, value, path, setter in data_container.iter_setters():

        if value is None:
            _type = 'none'
        elif isinstance(value, (int, float)):
            _type = 'number'
        elif value.isdigit():
            _type = 'number'
        else:
            _type = 'string'

        result.append('%s=%s' % (key.encode(DEFAULT_ENCODING), _type))

    return '&'.join(result)


def clean_fuzzable_request(fuzzable_request, dc_handler=clean_data_container):
    """
    We receive a fuzzable request and output includes the HTTP method and
    any parameters which might be sent over HTTP post-data in the request
    are appended to the result as query string params.

    :param fuzzable_request: The fuzzable request instance to clean
    """
    res = '(%s)-' % fuzzable_request.get_method().upper()
    res += clean_url(fuzzable_request.get_uri(), dc_handler=dc_handler)

    raw_data = fuzzable_request.get_raw_data()

    if raw_data:
        res += '!' + dc_handler(raw_data)

    return res


def clean_fuzzable_request_form(fuzzable_request, dc_handler=clean_data_container):
    """
    This function will extract data from the fuzzable request and serialize it.

    The main goal of this function is to return a "unique representation"
    of how the HTTP request looks like WITHOUT including the URL.

    Related with https://github.com/andresriancho/w3af/issues/15970

    :param fuzzable_request: The fuzzable request instance to clean
    """
    # Method
    res = [fuzzable_request.get_method().upper()]

    # Type
    raw_data = fuzzable_request.get_raw_data()
    res.append(raw_data.get_type())

    # Query string parameters
    uri = fuzzable_request.get_uri()
    if uri.has_query_string():
        res.append(dc_handler(uri.querystring))
    else:
        res.append('')

    # Post-data parameters
    if raw_data:
        res.append(dc_handler(raw_data))
    else:
        res.append('')

    return '|'.join([smart_str_ignore(s) for s in res])


def clean_url(url, dc_handler=clean_data_container):
    """
    Clean a URL instance to string following these rules:
        * If there is a query string, leave the path+filename untouched and
          clean the query string only

        * Otherwise clean the path+filename

    :param url: URL instance
    :return: A "clean" representation of the URL
    """
    res = url.base_url().url_string.encode(DEFAULT_ENCODING)

    if url.has_query_string():
        res += url.get_path().encode(DEFAULT_ENCODING)[1:]
        res += '?' + dc_handler(url.querystring)
    else:
        res += clean_path_filename(url)

    return res


def clean_path_filename(url):
    """
    Clean the path+filename following these rules:
        * If the URL has a filename, we'll keep the path untouched
        * If the filename has an extension, we keep it untouched
        * When cleaning the path we only touch the last child path

    :param url: The URL instance
    :return: A clean URL string
    """
    filename = url.get_file_name().encode(DEFAULT_ENCODING)
    path = url.get_path_without_file().encode(DEFAULT_ENCODING)

    if filename:
        res = path[1:]
        res += clean_filename(filename)
    else:
        res = clean_path(url.get_path().encode(DEFAULT_ENCODING))[1:]

    return res


def clean_filename(filename):
    """
    Clean the URL filename (if any)
    :param filename: The URL filename
    :return: A "clean" representation of the filename we can use to compare
    """
    # Clean the filename
    split_fname = filename.rsplit('.', 1)
    split_fname[0] = FILENAME_TOKEN

    # Create the filename again
    return '.'.join(split_fname)


def clean_path(path):
    """
    Clean the URL path (if any)
    :param path: The URL path
    :return: A "clean" representation of the path we can use to compare
    """
    split_path = path.rsplit('/', 2)[:-1]

    if len(split_path) == 2:
        # We have a path, clean the last part of it
        split_path[1] = PATH_TOKEN

    return '/'.join(split_path) + '/'
