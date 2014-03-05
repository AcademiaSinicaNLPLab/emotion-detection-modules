# -*- coding: utf-8 -*-

## transform SVM output to our format

import pymongo, json, sys, os

svm_root = '/Users/Maxis/corpus/svm/'
svm_out_root  = os.path.join(svm_root, 'o')
our_out_root  = os.path.join(svm_root, 'our')

svm_out_file = 'LJ40K_TF-0xIDF-1_wn.b1c4.o'
our_out_file = svm_out_file.replace('.o','.txt')
svm_test_file = svm_out_file.split('.')[0] + '.test.txt'

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')

emotions = sorted([x['emotion'] for x in list(mc['LJ40K']['emotions'].find({'label':'LJ40K'}))])

## read test file to get gold answer
golds = [ emotions[ int(line.strip().split()[0]) ] for line in open(os.path.join(svm_root, svm_test_file), 'r')]

with open(os.path.join(our_out_root, our_out_file), 'w') as fw:

	for i, line in enumerate( open(os.path.join(svm_out_root, svm_out_file), 'r') ):
		line = line.strip().split()
		if line[0] == 'labels':
			labels = map(lambda x:emotions[int(x)], line[1:])
		else:
			gold = golds.pop(0)
			predict = emotions[int(line[0])]
			prob = dict( zip( labels, map(lambda x:float(x), line[1:]) ) )

			entry = '\t'.join( ['doc', gold, json.dumps(prob)] )
			# print i
			fw.write( entry + '\n' )



	