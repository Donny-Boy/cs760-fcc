import csv


# Initialize dataset
y = []
r = 0
for p in range(21):
    with open('v2/generated_3_' + str(p+1) + '.csv', 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            y.append(row[3813])
            r += 1
            if r % 1000 == 0:
                print(str(r) + ' rows read')
    print('read ' + str(p))

print(len(y))

for i in range(6):
    with open('v4/y_' + str(i) + '.csv', 'w+', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        for row in y:
            y_value = "".join(row)
            if float(y_value) != 0:
                writer.writerow([y_value])
    print('wrote ' + str(i))

