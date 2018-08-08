"""
constants.py

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
HTML_DOC = u"""
<html>
    <head>
        %(head)s
    </head>
    <body>
        %(body)s
    </body>
</html>
"""

META_REFRESH = u"""<meta http-equiv="refresh" content="600">"""
META_REFRESH_WITH_URL = u"""
<meta http-equiv="refresh" content="2;url=http://crawler.w3af.com/">"""
META_REFRESH_WITH_URL_AND_QUOTES = u"""
<meta http-equiv="refresh" content="2;url='http://crawler.w3af.com/'">"""

# Other templates
BASE_TAG = u"""
<base href="http://www.w3afbase.com">
<base target="_blank">
"""

# Form templates
FORM_METHOD_GET = u"""
<form method="GET" action="/index.php">
    %(form_content)s
</form>
"""
FORM_METHOD_POST = u"""
<form method="POST" action="/index.php">
    %(form_content)s
</form>
"""
FORM_WITHOUT_METHOD = u"""
<form action="/index.php">
    %(form_content)s
</form>
"""
FORM_WITHOUT_ACTION = u"""
<form method="POST">
    %(form_content)s
</form>
"""

FORM_MULTILINE_TAGS = u"""
<form  class="form-horizontal" method="post" ><input type='hidden' name='csrfmiddlewaretoken' value='UN2BDAoRUTtlWlFtNCTFtjLZsLRYQQ1E' /> <div id="div_id_input" class="control-group"><label for="id_input" class="control-label requiredField">
                What is your favorite food?<span class="asteriskField">*</span></label><div class="controls"><input class="form-control input-sm textinput textInput" id="id_input" maxlength="40" name="input" type="text" value="Burgers" /> </div></div><div
      style="padding: 10px;"><i class="icon-leaf"></i> Hint: <code>&lt;script&gt;alert(1)&lt;/script&gt;</code></div><div class="form-actions"><input type="submit"
    name="/xss"
    value="Submit"

        class="btn btn-primary btn-info pull-right"
        id="submit-id-xss"


    /> </div></form>
"""

# Textarea templates
TEXTAREA_WITH_NAME_AND_DATA = u"""\
<textarea name="sample_name">sample_value</textarea>"""

TEXTAREA_WITH_ID_AND_DATA = u"""\
<textarea id="sample_id">sample_value</textarea>"""

TEXTAREA_WITH_NAME_ID_AND_DATA = u"""\
<textarea name="sample_name" id="sample_id">sample_value</textarea>"""

TEXTAREA_WITH_NAME_EMPTY = u'<textarea name=""></textarea>'

# Input templates
INPUT_TEXT_WITH_NAME = u'<input name="foo1" type="text" value="bar">'
INPUT_TEXT_WITH_ID = u'<input id="foo2" type="text" value="bar">'
INPUT_FILE_WITH_NAME = u'<input name="foo3" type="file" value="bar">'
INPUT_SUBMIT_WITH_NAME = u'<input name="foo4" type="submit">'
INPUT_RADIO_WITH_NAME = u'<input name="foo5" type="radio" checked>'
INPUT_CHECKBOX_WITH_NAME = u'<input name="foo6" type="checkbox" checked="true">'
INPUT_HIDDEN = u'<input name="foo7" type="hidden" value="bar">'

# Select templates
SELECT_WITH_NAME = u"""
<select name="vehicle">
    <option value=""></option>
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
    </option>
</select>"""

SELECT_WITH_ID = u"""
<select id="vehicle">
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
</select>"""

# Anchor templates
A_LINK_RELATIVE = u'<a href="/index.php">XXX</a>'
A_LINK_ABSOLUTE = u'<a href="http://w3af.com/home.php">XXX</a>'
A_LINK_FRAGMENT = u'<a href="#mark">XXX</a>'
