#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Script to extract the overall vocabulary and bag-of-words counts
# from comment submissions to FCC proceedings 17-108.
#
# JSON submission files are expected to be found under
# ./FCC-SPAM-ECFS/ECFS_17-108_*/*.json
#
# bag-of-words json files are stored under ./bag-of-words

import glob
import json
import nltk
import os
import sys


def usage():
    sys.stderr.write("usage: bag-of-words.py\n")
    sys.exit(0)


def count_words_in_submission(submission):
    """
    Extracts comment content from FCC submissions and converts into word counts.

    :param submission: submission to the FCC proceedings (dict)
    :return: dictionary mapping words to the number of times they appear in the submission comment (dict)
    """
    counts = dict()
    submission_type = None
    try:
        submission_type = submission['submissiontype']['abbreviation']
    except:
        pass
    # Only process 'CO' (comment) and 'OP' (oppose) submissions
    if submission_type not in ['CO', 'OP']:
        return counts
    names = set()
    for filer in submission['filers']:
        names.update(filer['name'].lower().split())
    # Due to different ways comments are submitted, the content can appear under different JSON entries
    if 'text_data_docs' in submission:
        for doc in submission['text_data_docs']:
            counts = count_words(doc['data'], names, counts)
    if 'text_data' in submission:
        counts = count_words(submission['text_data'], names, counts)
    if 'addressentity' in submission and 'text_data' in submission['addressentity']:
        counts = count_words(submission['addressentity']['text_data'], names, counts)
    return counts


english_words = set(nltk.corpus.words.words())
stop_words = set(nltk.corpus.stopwords.words('english'))


def count_words(comment, names, counts):
    """
    Updates the word count dictionary based on words found in the comment.  Words must:
     * Be English words in the NLTK corpus module
     * Not appear in the NLTK list of stopwords.
     * Not be the filer(s) names

    For counting, all punctuation is removed an all characters lowercased.  Removing punctuation may
    cause valid contractions and hyphenations to become invalid English words.
    :param comment: comment being processing (str)
    :param names: list of filer(s) names to exclude from counting (str)
    :param counts: dictionary of word counts to update / expand (dict)
    :return: updated word counts dictionary (dict)
    """
    words = [word for word in nltk.wordpunct_tokenize(comment.lower())
             if word.isalpha() and word not in stop_words and word not in names and word in english_words]
    for word in words:
        if word not in counts:
            counts[word] = 0
        counts[word] += 1
    return counts


if __name__ == '__main__':
    if len(sys.argv) > 1:
        usage()

    print('starting...')
    outfile = sys.stdout
    vocabulary = set()
    vocab_path = os.path.join('.', 'bag-of-words', 'vocabulary.json')
    # Load the last saved vocabulary list when restarting processing
    if os.path.exists(vocab_path):
        with open(vocab_path) as vocab_file:
            vocabulary = set(json.load(vocab_file))
            sys.stdout.write('loaded {} vocabulary words\n'.format(len(vocabulary)))
    for src_path in glob.glob('./FCC-SPAM-ECFS/ECFS_17-108_*/*.json'):
        with open(src_path) as src_file:
            src_base = os.path.basename(src_path)
            sys.stdout.write(src_base)
            sys.stdout.flush()
            dst_path = os.path.join('.', 'bag-of-words', src_base)
            if os.path.exists(dst_path):
                sys.stdout.write(' [skipped]\n')
                sys.stdout.flush()
                continue
            with open(dst_path, 'w') as dst_file:
                outfile = dst_file
                outfile.write('[\n')
                separator = ''
                for i, submission in enumerate(json.load(src_file)):
                    if i % 100 == 0:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                    try:
                        bag = {'id_submission': submission['id_submission'],
                               'bag-of-words': count_words_in_submission(submission)}
                        # Keep a running list of all words seen
                        vocabulary.update(bag['bag-of-words'].keys())
                        outfile.write(separator + json.dumps(bag, indent=4))
                        separator = ',\n'
                    except Exception as exc:
                        sys.stderr.write('{}:{}: {}\n'.format(src_base, submission['id_submission'], exc))
                outfile.write('\n]\n')
            sys.stdout.write(' [done]\n')
            sys.stdout.write('vocab len: {}\n'.format(len(vocabulary)))
            sys.stdout.flush()
            # Atomically update the vocabulary file after processing each JSON file
            with open(vocab_path + '.new', 'w') as vocab_file:
                vocab_file.write(json.dumps(sorted(vocabulary), indent=4))
            os.rename(vocab_path + '.new', vocab_path)
