#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Script to extract standardized features from the
# comment submissions to FCC proceedings 17-108, driven by
# the Startup Policy Lab survey results.
#
# NOTE: Customize data extraction using the extract_spec.py module.
import sys
from lib.dataset import Dataset


def usage():
    sys.stderr.write("usage: extract-dataset.py\n")
    sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        usage()

    sys.stderr.write('starting...\n')
    dataset = Dataset()
    dataset.pull_points_from_survey()
    dataset.add_features_from_fcc()
    dataset.filter_one_hot_features()
    dataset.print_csv()
