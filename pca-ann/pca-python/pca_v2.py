import csv
import sys
import numpy as np


for dataset_id in range(5):
    print('Dataset: ' + str(dataset_id))

    # Read features list
    features = []
    i = 0
    with open('v2/features-list_5.csv', 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            if int(row[1]) <= dataset_id and int(row[1]) >= 0:
                features.append(i)
            i += 1
    print(len(features))

    # Initialize dataset
    dataset = []
    y_valid = []
    r = 0
    for p in range(21):
        with open('v2/generated_3_' + str(p+1) + '.csv', 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                dataset.append([float(row[i]) for i in features])
                y_valid.append(float(row[3813]) != 0)
                r += 1
                #if r % 10000 == 0:
                #    print(str(r) + ' rows read')
        #print('read ' + str(p))

    print(len(dataset))

    X = np.array(dataset).astype(np.float)
    mu = np.mean(X, axis=0)
    sigma = np.std(X, axis=0)
    sigma = np.where(sigma==0, 1, sigma)
    X_norm = (X - mu) / sigma

    print(np.shape(X_norm))

    m, n = np.shape(X_norm)
    Sigma = (1/m)*(X_norm.T@X_norm)
    U,s,VT = np.linalg.svd(Sigma)

    desired_var = float(sys.argv[1])
    K = 0
    total_var = np.sum(s)
    current_var = 0
    for k in range(len(s)):
        current_var += s[k]
        var_retained = current_var / total_var
        if var_retained >= desired_var:
            K = k + 1
            break

    Ureduce = U[:,:K]
    X_valid = X_norm[y_valid]
    Z = X_valid@Ureduce

    print(np.shape(Ureduce))
    print(np.shape(Z))

    np.savetxt('v5/U/U_' + str(dataset_id) + '.csv', Ureduce, fmt='%.8f', delimiter=',')
    np.savetxt('v5/X_PCA_' + str(dataset_id) + '.csv', Z, fmt='%.8f', delimiter=',')
    np.savetxt('v5/X_Orig_' + str(dataset_id) + '.csv', X[y_valid], fmt='%.8f', delimiter=',')

    print(str(np.shape(X_valid)[1]) + '->' + str(K))
