import csv
import math


max_rows = 6500
i = 0
f = 1
with open('v2/generated_3.csv', 'r') as ifile:
    reader = csv.reader(ifile, delimiter=',')
    next(reader)
    for row in reader:
        if i % max_rows == 0:
            print('created ' + str(f))
            ofile = open('v2/generated_3_' + str(f) + '.csv', 'w+', newline='')
            writer = csv.writer(ofile, delimiter=',')
        writer.writerow(row)
        i += 1
        if i % 1000 == 0:
            print(str(i) + ' rows written')
        if i % max_rows == 0:
            print('finished ' + str(f))
            f += 1
            ofile.close()
            i = 0
    ofile.close()
print(str(f) + ' files created')
