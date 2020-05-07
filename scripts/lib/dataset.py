#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
import csv
import glob
import json
import os
import sys

from extract_spec import *
from lib import standardize

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
standard_combined_path = os.path.join(datasets_path,
                                      'standard-combined', 'example',
                                      'dataset.csv')


class Dataitem(dict):
    """
    Collects selected features from the source datasets
    """
    one_hot_counts = dict()

    def __init__(self, _hash):
        super().__init__()
        if not _hash:
            _hash = 'MISSING'
        self._hash = _hash
        self._id = None
        self._bag_of_words = None
        self._comment = None

    def add_features(self, row, features):
        for feature, element in features.items():
            feature_value = standardize.element(element, row)
            if element['one-hot']:
                if feature not in self.one_hot_counts:
                    self.one_hot_counts[feature] = {'_spec': element}
                feature_counts = self.one_hot_counts[feature]
                feature = feature + '.' + str(feature_value)
                if feature not in feature_counts:
                    feature_counts[feature] = 0
                feature_counts[feature] += 1
                self[feature] = 1.0
            else:
                self[feature] = feature_value

    def add_bag_of_words(self, word_counts):
        for word in word_counts:
            feature = 'text.' + word
            self[feature] = float(word_counts[word])

    def add_all(self, row):
        self.update(row)
        return row.keys()

    def get_hash(self):
        return self._hash

    def get_id(self):
        return self._id

    def set_id(self, _id):
        self._id = _id

    def get_campaign(self):
        campaigns = [campaign_key for campaign_key in self if campaign_key.startswith('campaign.')]
        if not campaigns:
            return None
        return campaigns[0]

    def set_comment(self, comment):
        self._comment = comment

    def get_comment(self):
        return self._comment


def load_email_index():
    with open(email_hash_index_path) as index_file:
        return json.load(index_file)


def make_point_from_survey_row(row, line_num):
    """
    Create items from the Startup Policy Lab survey.
    To be included, an item must have:
     * a valid email_hash
     * One of:
       - a survey response (active email address)
       - the email bounced (bogus / inactive email address)
       - the email send failed (bogus email address)

    :return: None
    """
    # Skip items without a valid e-mail hash.
    if not extract_survey_no_response and ['email_valid'] != 'True':
        return None
    # Skip items with no response and no indication of failure
    survey_not_commenter = standardize.element(survey_not_commenter_feature, row)
    survey_bounced = standardize.element(survey_bounced_feature, row)
    survey_send_failed = standardize.element(survey_send_failed_feature, row)
    survey_comment = standardize.count_words(row['short_comment'])
    if extract_survey_no_response:
        if survey_not_commenter not in standardize.exception_values and survey_not_commenter != 0.0:
            return None
    elif ((survey_not_commenter in standardize.exception_values or survey_not_commenter == 0.0) and
            (survey_bounced in standardize.exception_values or survey_bounced != 1.0) and
            (survey_send_failed in standardize.exception_values or survey_send_failed != 1.0)):
        return None
    try:
        item = Dataitem(row['email_hash'])
    except ValueError as exc:
        sys.stderr.write("{}: {}\n".format(line_num, exc))
        return None
    item.set_comment(survey_comment)
    item.add_features(row, survey_features)
    return item


class Dataset(list):
    """
    Used to compile a dataset extracted/generated from the source datasets.
    """
    def __init__(self):
        super().__init__()
        self.features = set()
        self.by_hash = dict()
        self.by_json = None
        self.by_submitted = dict()
        self.bins_by_campaign = dict()
        self.all_bins = dict()
        self.vocabulary = dict()

    def initialize_from_csv(self, path, item_factory=None):
        """
        Create an initial set of data items based on data in
        the specified CSV file.  The 'email_hash' feature is required.

        :param path: Location of the CSV file
        :param item_factory: Optional function to filter and standardize
                             items found in the CSV file.  If not provided,
                             all items are included verbatim.
        :return:
        """
        sys.stderr.write(os.path.basename(path))
        sys.stderr.flush()
        with open(path, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            num_cols = len(reader.fieldnames)
            for i, row in enumerate(reader):
                if i % 10000 == 0:
                    sys.stderr.write('.')
                    sys.stderr.flush()
                if len(row) == num_cols:
                    if item_factory is not None:
                        item = item_factory(row, reader.line_num)
                        if item is None:
                            continue
                    else:
                        item = Dataitem(row['email_hash'])
                        item.add_all(row)
                    # Build the master list of features (used for column headers)
                    self.features.update(item.keys())
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

    def pull_points_from_survey(self):
        """
        Create initial data set items from the Startup Policy Lab survey dataset.

        :return: None
        """
        self.initialize_from_csv(survey_csv_path, item_factory=make_point_from_survey_row)

    def _add_to_submitted_bins(self, submitted, campaign=None):
        """
        Updates submitted bin counts.

        :param submitted: Timestamp when item was submitted (float)
        :param campaign: One-hot campaign feature associated with the item (string)
        :return: None
        """
        if extract_submitted_bin_minutes is None:
            return
        submitted_bin = int(submitted / 60) * 60
        if campaign is not None:
            if campaign not in self.bins_by_campaign:
                self.bins_by_campaign[campaign] = dict()
            campaign_bins = self.bins_by_campaign[campaign]
            if submitted_bin not in campaign_bins:
                campaign_bins[submitted_bin] = 0
            campaign_bins[submitted_bin] += 1
        if submitted_bin not in self.all_bins:
            self.all_bins[submitted_bin] = 0
        self.all_bins[submitted_bin] += 1

    def add_features_from_bins(self):
        """
        Adds time-submitted bin count features to each item in the dataset.

        :return: None
        """
        if extract_submitted_bin_minutes is None:
            return
        submitted_bin_seconds = 60 * extract_submitted_bin_minutes
        for item in self:
            submitted = int(item['submitted'])
            submitted_bin_base = int(submitted / submitted_bin_seconds) * submitted_bin_seconds
            centered_bin_base = int((submitted - (submitted_bin_seconds / 2)) / 60) * 60
            campaign = item.get_campaign()
            campaign_bins = self.bins_by_campaign[campaign]
            item['campaign_submitted_bin'] = sum([campaign_bins[submitted_bin]
                                                  for submitted_bin in range(submitted_bin_base,
                                                                             submitted_bin_base + submitted_bin_seconds,
                                                                             60)
                                                  if submitted_bin in campaign_bins])
            item['campaign_centered_bin'] = sum([campaign_bins[submitted_bin]
                                                for submitted_bin in range(centered_bin_base,
                                                                           centered_bin_base + submitted_bin_seconds,
                                                                           60)
                                                if submitted_bin in campaign_bins])
            item['all_submitted_bin'] = sum([self.all_bins[submitted_bin]
                                             for submitted_bin in range(submitted_bin_base,
                                                                        submitted_bin_base + submitted_bin_seconds, 60)
                                             if submitted_bin in self.all_bins])
            item['all_centered_bin'] = sum([self.all_bins[submitted_bin]
                                           for submitted_bin in range(centered_bin_base,
                                                                      centered_bin_base + submitted_bin_seconds, 60)
                                           if submitted_bin in self.all_bins])
            self.features.update(['campaign_submitted_bin', 'campaign_centered_bin',
                                  'all_submitted_bin', 'all_centered_bin'])

    def add_features_from_fcc(self):
        """
        Add features from the FCC dataset to the dataset items.

        :return: None
        """
        self._load_json_buckets()
        for json_name in sorted(self.by_json):
            survey_items_in_json = self.by_json[json_name]
            sys.stderr.write(json_name)
            sys.stderr.flush()
            status = ' '
            items_found_in_json = dict()
            candidate_items = dict()
            with open(os.path.join(fcc_deidentified_path, json_name)) as json_file:
                for i, submission in enumerate(json.load(json_file)):
                    if i % 1000 == 0:
                        sys.stderr.write(status)
                        sys.stderr.flush()
                        status = '.'
                    item = self._find_item(survey_items_in_json, submission)
                    if item is None:
                        candidate_items.update(self._find_candidates(submission))
                    else:
                        items_found_in_json[item.get_id()] = item
                        item.add_features(submission, fcc_features)
                        self.features.update(item.keys())
                        status = '+'

            # Add bag-of-words features if specified.
            if extract_bag_of_words_vocabulary is not None and (items_found_in_json or candidate_items):
                sys.stderr.write(status)
                sys.stderr.flush()
                status = ' '
                with open(os.path.join(fcc_bag_of_words_path, json_name)) as json_file:
                    for i, submission in enumerate(json.load(json_file)):
                        if i % 1000 == 0:
                            sys.stderr.write(status)
                            sys.stderr.flush()
                            status = '.'
                        submission_id = int(submission['id_submission'])
                        if submission_id in candidate_items:
                            item = self._find_item_by_comment(candidate_items[submission_id],
                                                              submission['bag-of-words'])
                            if item is not None:
                                items_found_in_json[submission_id] = item
                        if submission_id in items_found_in_json:
                            item = items_found_in_json[submission_id]
                            item.add_bag_of_words(submission['bag-of-words'])
                            self._update_vocabulary(submission['bag-of-words'])
                            status = 'v'
            sys.stderr.write(status + ' [done]\n')
            sys.stderr.flush()

        # Generate time-submitted bin features.
        self.add_features_from_bins()

        # Select the top vocabulary features to include.
        self.add_features_from_vocabulary()

    def filter_one_hot_features(self):
        """
        Select one-hot-features such that any specified 'one-hot-limit'
        is honored for that feature.

        :return: None
        """
        for feature, counts in Dataitem.one_hot_counts.items():
            spec = counts['_spec']
            del counts['_spec']
            if 'one-hot-limit' in spec:
                # keep values with the most occurrences up to the feature limit
                limit = spec['one-hot-limit']
                if len(counts) > limit:
                    # get a list of values sorted in decreasing order
                    top_values = sorted(counts, key=lambda value: counts[value], reverse=True)
                    last = limit - 1
                    last_count = counts[top_values[limit]]
                    # walk backwards to find where the count changes
                    while counts[top_values[last]] == last_count:
                        last -= 1
                    # grab the values up to where the count changes
                    one_hot_values = set(top_values[:last+1])
                    # remove the over-limit features
                    self.features -= (counts.keys() - one_hot_values)
                    sys.stderr.write('{} one-hot {} features added.\n'.format(len(one_hot_values), feature))

    def _update_vocabulary(self, word_counts):
        """
        Update vocabulary word counts with counts from an included dataset item.

        :param word_counts: item's bag-of-word counts
        :return: None
        """
        for word in word_counts:
            feature = 'text.' + word
            if feature not in self.vocabulary:
                self.vocabulary[feature] = 0
            self.vocabulary[feature] += word_counts[word]

    def add_features_from_vocabulary(self):
        """
        Add top most frequently seen words to the dataset features.

        :return: None
        """
        if not extract_bag_of_words_vocabulary:
            return
        self.features.update(sorted(self.vocabulary, key=lambda word: self.vocabulary[word],
                                    reverse=True)[:extract_bag_of_words_vocabulary])

    def _initialize_all_json_buckets(self):
        """
        Causes all json files to be scanned instead of just those that reference
        selected email_hash values.

        :return: None
        """
        for json_name in [os.path.basename(json_path)
                          for json_path in glob.glob(os.path.join(fcc_deidentified_path, '*'))]:
            self.by_json[json_name] = dict()

    def _load_json_buckets(self):
        """
        Build the mapping of json file names to Dataitems containing email_hashes found in those files.

        :return: None
        """
        self.by_json = dict()
        sys.stderr.write("loading json buckets ...")
        sys.stderr.flush()
        # Use the pre-built map of email_hash to json files that reference the hash
        index = load_email_index()
        if extract_submitted_bin_minutes:
            self._initialize_all_json_buckets()
        for item in self:
            if item.get_hash() in index:
                for json_name in index[item.get_hash()]:
                    if json_name not in self.by_json:
                        self.by_json[json_name] = dict()
                    if item.get_hash() not in self.by_json[json_name]:
                        self.by_json[json_name][item.get_hash()] = self.by_hash[item.get_hash()]
            else:
                submitted = str(int(item['submitted']))
                if submitted not in self.by_submitted:
                    self.by_submitted[submitted] = []
                self.by_submitted[submitted].append(item)
        sys.stderr.write(' {} buckets loaded\n'.format(len(self.by_json)))
        sys.stderr.flush()

    def _find_item(self, hash_items, submission):
        """
        Find an unclaimed item with a matching email_hash and a submission datestamp within one second.
        As a side-effected, updates time-submitted bins based on the submission being researched.

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
                    self._add_to_submitted_bins(submission_date, campaign=item.get_campaign())
                    return item
        self._add_to_submitted_bins(submission_date)
        return None

    def _find_candidates(self, submission):
        submission_date = standardize.element(fcc_submitted_feature, submission)
        submission_id = standardize.element(fcc_id_feature, submission)
        submitted = str(int(submission_date))
        if submitted in self.by_submitted:
            return {
                submission_id: {
                    'items': self.by_submitted[submitted],
                    'submission': submission
                }
            }
        return {}

    def _find_item_by_comment(self, candidates, bag_of_words):
        for item in candidates['items']:
            comment_bag = item.get_comment()
            submission = candidates['submission']
            if len(comment_bag.keys() - bag_of_words.keys()) < 5:
                submission_id = standardize.element(fcc_id_feature, submission)
                submission_date = standardize.element(fcc_submitted_feature, submission)
                item.set_id(submission_id)
                self._add_to_submitted_bins(submission_date, campaign=item.get_campaign())
                item.add_features(candidates['submission'], fcc_features)
                self.features.update(item.keys())
                candidates['items'].remove(item)
                return item
        return None

    def print_csv(self):
        """
        Write the extracted dataset as a CSV on stdout.

        :return: None
        """
        fieldnames = sorted(self.features)
        unmatched_items = 0
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction='ignore', restval=0.0)
        writer.writeheader()
        for item in self:
            if item.get_id() is not None:
                writer.writerow(item)
            else:
                unmatched_items += 1
        if unmatched_items != 0:
            sys.stderr.write('found {} unmatched items\n'.format(unmatched_items))
