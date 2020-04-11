#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Script to extract standardized features from the
# comment submissions to FCC proceedings 17-108, driven by
# the Startup Policy Lab survey results.
#
# NOTE: Customize data extraction using the extract_spec.py module.
import csv
import json
import os
import sys

from extract_spec import *


def usage():
    sys.stderr.write("usage: extract-dataset.py\n")
    sys.exit(0)


# Location of the source datasets.  By default, look in 'datasets'
# under the current working directory.  Can be changed with the
# DATASETS_PATH environment variable.

datasets_path = 'datasets'
if 'DATASETS_PATH' in os.environ:
    datasets_path = os.environ['DATASETS_PATH']
survey_csv_path = os.path.join(datasets_path,
                               'startuppolicylab',
                               'deidentified_survey_results.csv')
email_hash_index_path = os.path.join(datasets_path,
                                     'indices',
                                     'contact_email.json')
fcc_deidentified_path = os.path.join(datasets_path,
                                     'fcc-deidentified', 'v1')
fcc_bag_of_words_path = os.path.join(datasets_path,
                                     'fcc-bag-of-words', 'v1')


class Dataitem(dict):
    """
    Collects selected features from the source datasets
    """
    def __init__(self, _hash):
        super().__init__()
        if not _hash:
            raise ValueError("empty hash")
        self._hash = _hash
        self._id = None

    def add_features(self, row, features):
        added_features = set()
        for feature, element in features.items():
            feature_value = standardize.element(element, row)
            if element['one-hot']:
                feature = feature + '.' + str(feature_value)
                self[feature] = 1.0
            else:
                self[feature] = feature_value
            added_features.add(feature)
        return added_features

    def get_hash(self):
        return self._hash

    def get_id(self):
        return self._id

    def set_id(self, _id):
        self._id = _id


def load_email_index():
    with open(email_hash_index_path) as index_file:
        return json.load(index_file)


class Dataset(list):
    """
    Used to compile a dataset extracted from the source datasets.
    """
    def __init__(self):
        super().__init__()
        self.features = set()
        self.by_hash = dict()
        self.by_json = None

    def pull_points_from_survey(self):
        """
        Create initial dataset from the Startup Policy Lab survey.
        To be included, an item must have:
         * a valid email_hash
         * One of:
           - a survey response (active email address)
           - the email bounced (bogus / inactive email address)
           - the email send failed (bogus email address)

        :return: None
        """
        sys.stderr.write(os.path.basename(survey_csv_path))
        sys.stderr.flush()
        with open(survey_csv_path, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            num_cols = len(reader.fieldnames)
            for i, row in enumerate(reader):
                if i % 10000 == 0:
                    sys.stderr.write('.')
                    sys.stderr.flush()
                if len(row) == num_cols:
                    # Skip items without a valid e-mail hash.
                    if row['email_valid'] != 'True':
                        continue
                    try:
                        item = Dataitem(row['email_hash'])
                    except ValueError as exc:
                        sys.stderr.write("{}: {}\n".format(reader.line_num, exc))
                        continue
                    added_features = item.add_features(row, survey_features)
                    # Skip items with no response and not indication of failure
                    if (item['not_commenter'] in standardize.exception_values and
                            (item['bounced'] in standardize.exception_values or item['bounced'] == 0.0) and
                            (item['send_failed'] in standardize.exception_values or item['send_failed'] == 0.0)):
                        continue
                    # Build the master list of features (used for column headers)
                    self.features.update(added_features)
                    # Build the master list of items
                    self.append(item)
                    # Build a mapping of email_hash to items containing that hash
                    if item.get_hash() not in self.by_hash:
                        self.by_hash[item.get_hash()] = list()
                    self.by_hash[item.get_hash()].append(item)
                    if extract_max is not None and len(self) == extract_max:
                        break
                else:
                    sys.stderr.write("{}: malformed row\n".format(reader.line_num))
        sys.stderr.write(" [done] {} items\n".format(len(self)))
        sys.stderr.flush()

    def add_features_from_fcc(self):
        """
        Add features from the FCC dataset to the Dataitems created from the
        survey dataset.

        :return: None
        """
        self._load_json_buckets()
        for json_name in sorted(self.by_json):
            hash_items = self.by_json[json_name]
            sys.stderr.write(json_name)
            sys.stderr.flush()
            status = ' '
            with open(os.path.join(fcc_deidentified_path, json_name)) as json_file:
                for i, submission in enumerate(json.load(json_file)):
                    if i % 1000 == 0:
                        sys.stderr.write(status)
                        sys.stderr.flush()
                        status = '.'
                    item = self._find_item(hash_items, submission)
                    if item is not None:
                        self.features.update(item.add_features(submission, fcc_features))
                        status = '+'
            sys.stderr.write(' [done]\n')
            sys.stderr.flush()

    def _load_json_buckets(self):
        """
        Build the mapping of json file names to Dataitems containing email_hashes found in those files.

        :return: None
        """
        self.by_json = dict()
        sys.stderr.write("loading json buckets ...")
        sys.stderr.flush()
        # Use the pre-build index of email_hash to json files that reference that hash
        index = load_email_index()
        for item in self:
            for json_name in index[item.get_hash()]:
                if json_name not in self.by_json:
                    self.by_json[json_name] = dict()
                if item.get_hash() not in self.by_json[json_name]:
                    self.by_json[json_name][item.get_hash()] = self.by_hash[item.get_hash()]
        sys.stderr.write(' {} buckets loaded\n'.format(len(self.by_json)))
        sys.stderr.flush()

    def _find_item(self, hash_items, submission):
        """
        Find an unclaimed item with a matching email_hash and a submission datestamp within one second.

        :param hash_items: items indexed by email_hash (dict)
        :param submission: fcc submission data (dict)
        :return: claimed item from hash_items
        """
        submission_hash = standardize.element(fcc_email_hash_feature, submission)
        submission_date = standardize.element(fcc_submitted_feature, submission)
        submission_id = standardize.element(fcc_id_feature, submission)
        if submission_hash in hash_items:
            for item in hash_items[submission_hash]:
                if item.get_id() is None and abs(submission_date - item['submitted']) <= 1:
                    item.set_id(submission_id)
                    return item
        return None

    def print_csv(self):
        """
        Write the extracted dataset as a CSV on stdout.

        :return: None
        """
        fieldnames = sorted(self.features)
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, restval=0.0)
        writer.writeheader()
        for item in self:
            writer.writerow(item)
            if item.get_id() is None:
                raise RuntimeError("unmatched item")
            if item['email_hash'] in standardize.exception_values:
                raise RuntimeError("invalid hash")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        usage()

    sys.stderr.write('starting...\n')
    dataset = Dataset()
    dataset.pull_points_from_survey()
    dataset.add_features_from_fcc()
    dataset.print_csv()
