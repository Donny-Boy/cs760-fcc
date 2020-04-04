#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Script to remove personally identifiable information (pii) from
# comment submissions to FCC proceedings 17-108.
#
# JSON submission files are expected to be found under
# ./FCC-SPAM-ECFS/ECFS_17-108_*/*.json
#
# Deidentified files are stored under ./deidentified, skipping any files
# that already exist to permit restarting the script after interruption.

import glob
import hashlib
import json
import os
import sys


def usage():
    sys.stderr.write("usage: deidentify.py")
    sys.exit(0)


def validate(key, value):
    """
    Validate a particular element in the JSON data using custom code.
    Raises ValueError when validation fails.

    :param key: key of item being validated
    :param value: value found in submission
    :return: None
    """
    if key == 'proceedings':
        if value == '17-108' or isinstance(value, list) and any([proceeding['name'] == '17-108'
                                                                 for proceeding in value]):
            return
    raise ValueError('invalid "{}": "{}"'.format(key, str(value)))


def sha256hash(key, value):
    """
    Replace a particular element in the JSON data with the SHA256 hexdigest.

    :param key: key of the item being hashed
    :param value: value found in the submission
    :return: hexdigest of hashed value
    """
    if not isinstance(value, str):
        raise ValueError('invalid "{}": "{}"'.format(key, str(value)))
    if not value:
        return value
    return hashlib.sha256(value.encode('ascii', 'xmlcharrefreplace')).hexdigest()


def md5hash(key, value):
    """
    Replace a particular element in the JSON data with the MD5 hexdigest

    :param key: key of the item being hashed
    :param value: value found in the submission
    :return: hexdigest of hashed value
    """
    if not isinstance(value, str):
        raise ValueError('invalid "{}": "{}"'.format(key, str(value)))
    if not value:
        return value
    return hashlib.md5(value.encode('ascii', 'xmlcharrefreplace')).hexdigest()


# Dict of submission items containing PII in the following format:
#   'item_key': [is_required, None | deidentify_method | nested_items_dict, alternate_item]
deidentify_items = {
    'addressentity': [True, {
        'address_line_1': [False, sha256hash],
        'address_line_2': [False, sha256hash],
        'address_line_3': [False, sha256hash],
        'contact_email': [False, md5hash]
    }, 'internationaladdressentity'],
    'filers': [True, None],
    'proceedings': [True, validate],
    'text_data': [False, None],
    'text_data_docs': [False, None],
    'internationaladdressentity': [False, {
        'addresstext': [False, sha256hash]
    }],
    'contact_email': [False, md5hash]
}


def deidentify(comment, attributes=None):
    if attributes is None:
        attributes = deidentify_items
    for key, value in attributes.items():
        if key in comment:
            value = value[1]
            if value is None:
                del comment[key]
            elif isinstance(value, dict):
                if not isinstance(comment[key], dict):
                    raise ValueError('invalid "{}": "{}"'.format(key, str(value)))
                deidentify(comment[key], attributes=value)
            elif isinstance(value, str):
                comment[key] = value
            else:
                comment[key] = value(key, comment[key])
        elif value[0]:
            if len(value) != 3 or value[2] not in comment:
                raise ValueError('missing "{}": {}'.format(key, json.dumps(comment, indent=4)))


if __name__ == '__main__':
    print('starting...')
    outfile = sys.stdout
    for src_path in glob.glob('./FCC-SPAM-ECFS/ECFS_17-108_*/*.json'):
        with open(src_path) as src_file:
            sys.stdout.write(os.path.basename(src_path))
            dst_path = os.path.join('.', 'deidentified', os.path.basename(src_path))
            if os.path.exists(dst_path):
                sys.stdout.write(' [skipped]\n')
                continue
            with open(dst_path, 'w') as dst_file:
                outfile = dst_file
                outfile.write('[\n')
                separator = ''
                for i, comment in enumerate(json.load(src_file)):
                    if i % 100 == 0:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                    try:
                        deidentify(comment)
                        outfile.write(separator + json.dumps(comment, indent=4))
                        separator = ',\n'
                    except Exception as exc:
                        sys.stderr.write('{}: {}\n'.format(comment['id_submission'], exc))
                outfile.write('\n]\n')
            sys.stdout.write(' [done]\n')
