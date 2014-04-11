import pymongo
from collections import Counter, defaultdict

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']

Matrix = defaultdict(Counter)

# pattern id
Pid = {}

# emotion id
Eid = dict([(e,i) for (i,e) in enumerate(sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'})]))])

# gold 
Gold = {}

for doc in db['pats'].find():
	
	pat = doc['pattern']
	if pat not in Pid:
		last_pid = len(Pid)
		Pid[pat] = last_pid + 1 # start from 1

	pid = Pid[pat]
	udocID = doc['udocID']

	Gold[udocID] = Eid[doc['emotion']]

	Matrix[udocID][pid] += 1

with open('pattern.train.txt', 'w') as fw:

	for udocID in Matrix.keys():
		
		feature = ' '.join([str(k)+':'+str(v) for (k,v) in sorted(Matrix[udocID].items())])
		gold = str(Gold[udocID])
		line = ' '.join([gold, feature]) + '\n'

		fw.write(line)
