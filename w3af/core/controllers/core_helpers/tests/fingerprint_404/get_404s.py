import urllib2
import os
import zipfile
import shelve
import sys


ALEXA_TOP1M = 'http://s3.amazonaws.com/alexa-static/top-1m.csv.zip'
ALEXA_FILE = 'top-1m.csv'
ALEXA_FILE_COMPRESSED = 'top-1m.csv.zip'

if __name__ == '__main__':
    if not os.path.exists(ALEXA_FILE_COMPRESSED):
        resp = urllib2.urlopen(ALEXA_TOP1M)
        file(ALEXA_FILE, 'w').write(resp.read())

    if not os.path.exists(ALEXA_FILE):
        zfile = zipfile.ZipFile(ALEXA_FILE_COMPRESSED)
        zfile.extract(ALEXA_FILE, '.')

    s = shelve.open('data.shelve')

    # This is a "resume" feature
    last = len(s)
    print 'c(%s)' % last,

    for i, line in enumerate(file(ALEXA_FILE)):
        if i <= last:
            continue

        line = line.strip()
        _, domain = line.split(',')

        try:
            ok = urllib2.urlopen('http://%s/' % domain).read()
            try:
                bad = urllib2.urlopen('http://%s/not-ex1st.html' % domain).read()
            except urllib2.HTTPError, error:
                bad = error.read()
        except KeyboardInterrupt:
            break
        except urllib2.HTTPError:
            sys.stdout.write('4')
            sys.stdout.flush()
        except Exception:
            sys.stdout.write('E')
            sys.stdout.flush()
        else:
            s[domain] = (ok, bad)
            sys.stdout.write('.')
            sys.stdout.flush()

    sys.stdout.write('\n')
    s.close()
