"""
main.py

Copyright 2006 Andres Riancho

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
from w3af.core.data.context.utils.byte_chunk import ByteChunk
from .finders import (HtmlAttrSingleQuote, HtmlAttrDoubleQuote,
                      HtmlAttrBackticks, HtmlAttr, HtmlTag, HtmlText,
                      HtmlComment, ScriptMultiComment, ScriptLineComment,
                      ScriptSingleQuote, ScriptDoubleQuote, ScriptText,
                      StyleText, StyleComment, StyleSingleQuote,
                      StyleDoubleQuote)


def get_contexts():
    contexts = [HtmlAttrSingleQuote(), HtmlAttrDoubleQuote(),
                HtmlAttrBackticks(), HtmlAttr(), HtmlTag(), HtmlText(),
                HtmlComment(), ScriptMultiComment(), ScriptLineComment(),
                ScriptSingleQuote(), ScriptDoubleQuote(), ScriptText(),
                StyleText(), StyleComment(), StyleSingleQuote(),
                StyleDoubleQuote()]
    #contexts.append(HtmlAttrDoubleQuote2ScriptText())
    return contexts


def get_context(data, payload):
    """
    :return: A list which contains lists of contexts
    """
    return [c for c in get_context_iter(data, payload)]


def get_context_iter(data, payload):
    """
    :return: A context iterator
    """
    chunks = data.split(payload)
    data = ''

    for chunk in chunks[:-1]:
        data += chunk

        byte_chunk = ByteChunk(data)
        print byte_chunk

        for context in get_contexts():
            if context.match(byte_chunk):
                context.save(data)
                yield context
