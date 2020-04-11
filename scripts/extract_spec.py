#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Specification for what to extract from source datasets.
# Customize this file to adjust dataset extraction.

import standardize

# Maximum number of instances to extract.  None => extract all.
# This is useful when testing changes to the spec.  It takes about
# 30 minutes to perform a full extraction.
# extract_max = 1000
extract_max = None

# These dictionaries define how to extract values from the source datasets
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

fcc_features = {
    'email_hash': fcc_email_hash_feature,
    'id_submission': fcc_id_feature,
    'city_state': {
        'one-hot': False,
        'definition': [[['addressentity', 'city'], ['addressentity', 'state']]],
        'filter': standardize.city_state
    },
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
    'submissiontype': {
        'one-hot': True,
        'definition': [[['submissiontype', 'abbreviation']],
                       [['submissiontype', 'type']]],
        'filter': standardize.string
    }
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
    'bounced': {
        'one-hot': False,
        'definition': [[['bounced_or_filtered']]],
        'filter': standardize.boolean
    },
    'send_failed': {
        'one-hot': False,
        'definition': [[['send_failed']]],
        'filter': standardize.boolean
    },
    'not_commenter': {
        'one-hot': False,
        'definition': [[['not_original_commenter']]],
        'filter': standardize.boolean
    }
}
