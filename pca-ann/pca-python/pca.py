import csv
import numpy as np
import sys


# Define key columns indexes
column_id = {
    'bounced': 0,
    'city_state': 43,
    'email_hash': 46,
    'id_submission': 47,
    'not_commenter': 48,
    'send_failed': 49,
    'submissiontype.co': 50
}

# Initialize dataset
dataset = []
i = 0
for p in range(int(sys.argv[4])):
    with open(sys.argv[1] + '_' + str(p+1) + '.csv', 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            dataset.append(row)
            i+=1
print(i)

# Convert city_state to number of occurrences
city_states = {}
for row in dataset:
    city_state = row[column_id['city_state']]
    city_states[city_state] = city_states.get(city_state, 0) + 1
city_states['EMPTY'] = 0

# Convert email_hash to number of occurrences
email_hashes = {}
for row in dataset:
    email_hash = row[column_id['email_hash']]
    email_hashes[email_hash] = email_hashes.get(email_hash, 0) + 1

# Remove rows where non_commenter == 0
if int(sys.argv[5]) == 1:
    dataset = [row for row in dataset if not row[column_id['not_commenter']] == '0.0']

# Output non_commenter to csv
with open(sys.argv[2] + '.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter=',')
    for row in dataset:
        writer.writerow([row[column_id['not_commenter']]])

# Remove unused features (non_commenter, id_submission, city_state and email_hash
# And append number of occurrence features
for row in dataset:
    row.pop(column_id['submissiontype.co'])
    row.pop(column_id['send_failed'])
    row.pop(column_id['not_commenter'])
    row.pop(column_id['id_submission'])
    row.append(email_hashes[row.pop(column_id['email_hash'])])
    row.append(city_states[row.pop(column_id['city_state'])])
    row.pop(column_id['bounced'])

X = np.array(dataset).astype(np.float)
mu = np.mean(X, axis=0)
sigma = np.std(X, axis=0)
sigma = np.where(sigma==0, 1, sigma)
X_norm = (X - mu) / sigma

print(np.shape(X_norm))

m, n = np.shape(X_norm)
Sigma = (1/m)*(X_norm.T@X_norm)
U,s,VT = np.linalg.svd(Sigma)

desired_var = 0.99
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
Z = X_norm@Ureduce

np.savetxt(sys.argv[3] + '.csv', Z, fmt='%.8f', delimiter=',')

print(K)
