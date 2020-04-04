#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Script that generates index files in JSON format mapping interesting submission data
# to the file where the submission is located.

import json
import os
import sys

indices = {}


def usage():
    sys.stderr.write("usage: index.py <json_file> [...]")


def update_index_for_keys(submission, file, index, keys):
    """
    Extract keys from the submission and insert into the index.

    :param submission: portion of submission where the keys are expected to exist (dict)
    :param file: name of the file where the submission was found (str)
    :param index: index to update with the key->file mapping (dict)
    :param keys: list of keys that contain data to be indexed (list)
    :return:  None
    """
    for key in keys:
        if isinstance(key, str) and key in submission and len(submission[key]) != 0:
            value = str(submission[key])
            if value not in index:
                index[value] = [file]
            elif index[value][-1] != file:
                index[value].append(file)
        elif isinstance(key, dict):
            for subkey in key:
                if subkey in submission:
                    update_index_for_keys(submission[subkey], file, index, key[subkey])


def update_indices(submission, file):
    """
    Search through the submission for data to be indexed.

    :param submission: a complete submission found in the json file (dict)
    :param file: name of the json file (str)
    :return: None
    """
    # Dict with an entry for each index being built, and the location of submission data to index.
    index_using = {
        'contact_email': ['contact_email', {'addressentity': ['contact_email']}],
        'id_submission': ['id_submission']
    }
    global indices
    for index, keys in index_using.items():
        if index not in indices:
            indices[index] = {}
        update_index_for_keys(submission, file, indices[index], keys)


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        usage()
        exit(1)

    print('starting...')
    outfile = sys.stdout
    # Build the indices in memory.
    # WARNING: This uses 8G memory to build the two indices.  If additional indices are needed, they should be built
    #          one at a time.
    for src_path in sys.argv[1:]:
        with open(src_path) as src_file:
            base_file = os.path.basename(src_path)
            sys.stdout.write(base_file)
            sys.stdout.flush()
            for i, submission in enumerate(json.load(src_file)):
                if i % 100 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                try:
                    update_indices(submission, base_file)
                except Exception as exc:
                    sys.stderr.write('{}:{}: {}\n'.format(base_file, submission['id_submission'], exc))
            sys.stdout.write(' [done]\n')
            sys.stdout.flush()

    for index, index_path in [(index, os.path.join('.', 'indices', index)) for index in indices]:
        with open(index_path + '.json', 'w') as index_file:
            outfile = index_file
            outfile.write(json.dumps(indices[index], indent=4) + '\n')
            # Free up the memory
            del indices[index]
