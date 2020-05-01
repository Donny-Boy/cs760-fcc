#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Specification for what to extract from source datasets.
# Customize this file to adjust dataset extraction.

from lib import standardize

# Maximum number of instances to extract.  None => extract all.
# This is useful when testing changes to the spec.  It takes about
# 30 minutes to perform a full extraction.

# extract_max = 100
extract_max = None

# extract_submitted_bin_minutes - The time range in minutes over which to
# count the number of submissions.  Set to None to disable.
# This adds four features to each feature vector:
# 'all_submitted_bin': The count of all submissions in the fcc-deidentified dataset
#   that were submitted in the same extract_submitted_bin_minutes interval.
# 'all_centered_bin': The count of all submissions in the fcc-deidentified dataset
#   that were submitted in the interval centered at the time the item was submitted.
# 'campaign_submitted_bin' and 'campaign_centered_bin': same as above, except only
#   counting instances from the same campaign.

extract_submitted_bin_minutes = 10

# extract_bag_of_words_vocabulary - Create features in each feature vector
# for the extract_bag_of_words_vocabulary number of most frequently seen words
# in comments included in the extracted dataset.  Set to None to disable.
# Features are named 'text.<word>'

extract_bag_of_words_vocabulary = 100

# The following dictionaries define how to extract values from the source datasets
# and convert them into standardized features.
# The key is the name of the feature. The value is another dictionary with the
# following entries:
# 'one-hot': Convert this multinomial feature into a one-hot vector.
# 'definition': A three-deep nested list.  The outer list contains candidate elements
#               listed in priority order to use for the standardized value.  If the first
#               element is present and valid, it is standardized and returned.
#               If not, the elements are inspected in order until a valid one is found.
#               The middle list defines elements that are to be concatenated.
#               The inner list defines nested elements in the source dictionary.
# 'filter': A function used to standardize the feature value

fcc_submitted_feature = {
    'one-hot': False,
    'definition': [[['date_submission']]],
    'filter': standardize.date
}

fcc_email_hash_feature = {
    'one-hot': False,
    'definition': [[['contact_email']],
                   [['addressentity', 'contact_email']]],
    'filter': standardize.md5hash
}

fcc_id_feature = {
    'one-hot': False,
    'definition': [[['id_submission']]],
    'filter': standardize.integer
}

fcc_submissiontype_feature = {
    'one-hot': False,
    'definition': [[['submissiontype', 'abbreviation']],
                   [['submissiontype', 'type']]],
    'filter': standardize.string
}

fcc_city_state_feature = {
    'one-hot': True,
    'one-hot-limit': 4000,
    'definition': [[['addressentity', 'city'], ['addressentity', 'state']]],
    'filter': standardize.city_state
}

fcc_features = {
    'email_hash': fcc_email_hash_feature,
    'id_submission': fcc_id_feature,
    'city_state': fcc_city_state_feature,
    'date_received': {
        'one-hot': False,
        'definition': [[['date_received']]],
        'filter': standardize.date
    },
    'submitted': fcc_submitted_feature,
    'date_disseminated': {
        'one-hot': False,
        'definition': [[['date_disseminated']]],
        'filter': standardize.date
    },
    'email_confirmation': {
        'one-hot': False,
        'definition': [[['emailConfirmation']]],
        'filter': standardize.boolean
    }
}

survey_bounced_feature = {
    'one-hot': False,
    'definition': [[['bounced_or_filtered']]],
    'filter': standardize.boolean
}

survey_not_commenter_feature = {
    'one-hot': False,
    'definition': [[['not_original_commenter']]],
    'filter': standardize.boolean
}

survey_send_failed_feature = {
    'one-hot': False,
    'definition': [[['send_failed']]],
    'filter': standardize.boolean
}

survey_features = {
    'campaign': {
        'one-hot': True,
        'definition': [[['campaign']]],
        'filter': standardize.integer
    },
    'submitted': {
        'one-hot': False,
        'definition': [[['submitted']]],
        'filter': standardize.date
    },
    'not_commenter': survey_not_commenter_feature
}
