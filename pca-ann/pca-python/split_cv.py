import csv
import numpy as np
import math
import random


nfolds = 10
n = 12818
test_n = int(0.2*n)

test_id = random.sample(range(n), test_n)

all_ncomps = ['PCA', 'Orig']
for ncomps in all_ncomps:
    if ncomps == 'PCA':
        datasets = range(5)
    else:
        datasets = range(5)
    for dataset in datasets:
        print('Started dataset ' + ncomps + '_' + str(dataset))

        np.random.seed(123456)

        X = []
        i = 0
        with open('v5/X_' + ncomps + '_' + str(dataset) + '.csv', 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if i not in test_id:
                    X.append(row)
                i += 1

        y = []
        i = 0
        with open('v5/y_' + str(dataset) + '.csv', 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if i not in test_id:
                    y.append(row)
                i += 1

        classes = ['1.0', '-1.0', '0.0']
        X_fold = [[] for i in range(nfolds)]
        y_fold = [[] for i in range(nfolds)]
        for c in classes:
            X_class = []
            for i in range(len(X)):
                if y[i][0] == c:
                    X_class.append(X[i])
            n = len(X_class)
            if n > 0:
                folds = np.random.choice(np.repeat(range(nfolds), math.ceil(n/nfolds)), n, replace=False)
                for i in range(n):
                    X_fold[folds[i]].append(X_class[i])
                    y_fold[folds[i]].append(c)

        for f in range(nfolds):
            with open('v5/cv/' + str(dataset) + '/' + ncomps + '/X_' + ncomps + '_' + str(dataset) + '_' + str(f+1) + '.csv', 'w+', newline='') as file:
                writer = csv.writer(file, delimiter=',')
                for row in X_fold[f]:
                    writer.writerow(row)
            with open('v5/cv/' + str(dataset) + '/' + ncomps + '/y_' + str(dataset) + '_' + str(f+1) + '.csv', 'w+', newline='') as file:
                writer = csv.writer(file, delimiter=',')
                for row in y_fold[f]:
                    writer.writerow([row])
            print(str(f) + ': ' + str(len(X_fold[f])) + ' ' + str(len(y_fold[f])))

        print('finished train')

        X_test = []
        i = 0
        with open('v5/X_' + ncomps + '_' + str(dataset) + '.csv', 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if i in test_id:
                    X_test.append(row)
                i += 1

        y_test = []
        i = 0
        with open('v5/y_' + str(dataset) + '.csv', 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if i in test_id:
                    y_test.append(row)
                i += 1

        with open('v5/cv/' + str(dataset) + '/' + ncomps + '/X_test_' + ncomps + '_' + str(dataset) + '.csv', 'w+', newline='') as file:
            writer = csv.writer(file, delimiter=',')
            for row in X_test:
                writer.writerow(row)
        with open('v5/cv/' + str(dataset) + '/' + ncomps + '/y_test_' + str(dataset) + '.csv', 'w+', newline='') as file:
            writer = csv.writer(file, delimiter=',')
            for row in y_test:
                writer.writerow(row)

        print('test: ' + str(len(X_test)) + ' ' + str(len(y_test)))

    print('end')
