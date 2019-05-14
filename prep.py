#!/usr/bin/python3

import sys, random

if len(sys.argv) != 2:
    print("Log file missing")
    sys.exit(0)

logs = []

with open(sys.argv[1],'r') as log:
    for line in log:
        logs.append(line)

to_extend = random.sample(logs, int(len(logs)/5)) # 20% of data
for i, val in enumerate(to_extend):
    vals = val.split(' ')
    vals[0] = str(float(random.randint(0, 1)))
    vals[1] = str(float(random.randint(0, 1)))
    vals[7] = '0.5'
    vals[8] = '0.5'
    logs.append(' '.join(vals)+"\n")

clean_logs = list(set(logs))
random.shuffle(clean_logs);

with open('train.txt','x') as train:
    for _, val in enumerate(clean_logs):
        train.write(val)

train.close()
log.close()