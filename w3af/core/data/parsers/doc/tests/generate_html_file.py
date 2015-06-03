#!/usr/bin/env python
import sys

SOME_TEXT = 'This is placeholder text'
OUTPUT_FILE = 'w3af/core/data/parsers/doc/tests/data/huge.html'


def main():
    """
    Generate a huge HTML file which is useful for testing parser performance,
    not really real-life data, but forces the parser to use a lot of memory
    if it loads the whole thing right away/keeps the tree in memory.

    :return: None, we write the file to data/huge.html
    """
    output = file(OUTPUT_FILE, 'w')
    write = lambda s: output.write('%s\n' % s)
    
    write('<html>')
    write('<title>%s</title>' % SOME_TEXT)

    write('<body>')

    #
    #   Long
    #
    for i in xrange(5000):
        write('<p>')
        write(SOME_TEXT)
        write('</p>')

        write('<p>')
        write(SOME_TEXT)
        write('<a href="/%s">%s</a>' % (i, SOME_TEXT))
        write('</p>')

        write('<div>')
        write('<a href="/%s">%s</a>' % (i, SOME_TEXT))
        write(SOME_TEXT)
        write('<form action="/%s" method="POST">' % i)
        write('<input type="text" name="abc-%s">' % i)
        write('</form>')
        write('</div>')

    #
    #   Long II
    #
    for i in xrange(5000):
        write('<div>')
        write('<img src="/img-%s" />' % i)
        write('<a href="mailto:andres%s@test.com">%s</a>' % (i, SOME_TEXT))
        write('</div>')

    #
    #   Deep
    #
    for i in xrange(5000):
        write('<div id="id-%s">' % i)
        write('<a href="/deep-div-%s">%s</a>' % (i, SOME_TEXT))

    for i in xrange(5000):
        write('<p>')
        write(SOME_TEXT)
        write('</p>')
        write('</div>')

    #
    #   Some scripts at the end
    #
    for i in xrange(50):
        write('<script><!-- code(); --></script>')

    write('</body>')
    write('</html>')


if __name__ == '__main__':
    sys.exit(main())
