
from pyroc import *

# sid = '538a9245d4388c7a1a54c294'
sid = '538bcfaad4388c59136665df'
param = 'c2g0.001t2'
# param = 'default'

AUC = {}

for i in range(40):

	predict = [float(line.split()[1]) for line in open('tmp/'+sid+'/'+str(i)+'.b.'+param+'.p.out').read().strip().split('\n')[1:]]
	gold = map(lambda x: 1 if int(x) == 1 else 0, open('tmp/'+sid+'/'+str(i)+'.b.gold').read().strip().split('\n'))

	# roc = random_sample)
	sample = sorted(zip(gold, predict), key=lambda x:x[0], reverse=True)
	roc = ROCData(sample)

	# print i, roc.auc()

	AUC[i] = roc.auc()


print sum(AUC.values())/float(len(AUC))