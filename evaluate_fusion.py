# -*- coding: utf-8 -*-
import sys
# sys.path.append('../')
import config
import color
import re
import pymongo, os
from collections import Counter, defaultdict
# from itertools import product
from pprint import pprint
import json


db = pymongo.Connection(config.mongo_addr)[config.db_name]

def accuracy(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return 0.0 if TP+TN+FN+FP == 0 else round((TP+TN)/float(TP+TN+FN+FP), 4)


def find_intersection(eval_mdoc,show=True):

	import pymongo, sys, os
	db = pymongo.Connection('doraemon.iis.sinica.edu.tw')["LJ40K"]
	LJ40K = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])
	Mishne05 = sorted([x['emotion'] for x in db['emotions'].find({'label':'Mishne05'}) ])

	inter = []
	for e in set(LJ40K+Mishne05):
		if e in LJ40K and e in Mishne05: inter.append(e)
		
	inter_accuracy = {}
	for e in eval_mdoc['accuracy']:
		if e in inter:
			inter_accuracy[e] = eval_mdoc['accuracy'][e]

	if show:
		pprint(eval_mdoc['accuracy'])

	print >> sys.stderr, 'avg accuracy in overall\t\t', eval_mdoc['avg_accuracy']
	print >> sys.stderr, 'avg accuracy in intersection\t', round( sum(inter_accuracy.values())/float(len(inter_accuracy.values())), 4)

	return 

def load(fn='cache/fusion.csv'):
	return [(line.strip().split()[0], map(lambda x:float(x), line.strip().split()[1:])) for line in open(fn).read().strip().split('\n')]

def evaluation(fn, k='binary'):

	# D = json.load(open('LJ40K_docid.json'))
	# test = open('idx_d.test.txt').read().strip().split('\r\n')
	# emotions = open('emolist.LJ40K.txt').read().strip().split('\n')

	# binary_results = [[1 if float(x) > 0.5 else 0 for x in line.split(',')] for line in open('raw/Yest_prob_te_mean_f1.csv').read().strip().split('\n')]
	# results = [[(emotions[i], x, True if float(x) > 0.5 else False) for i,x in enumerate(line.strip().split(','))] for line in open('raw/Yest_prob_te_mean_f1.csv').read().strip().split('\n')]
	
	data = load(fn)

	emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])

	# gold_emotions = map(lambda x:emotions[int(x[0])], data)
	# results = map(lambda x:x[1], data)

	Positive, Negative = True, False
	Results = defaultdict(list)


	## currently evaluate <target_emotion>
	for target_emotion in emotions:

		# print 'eval',target_emotion

		really_is_positive, really_is_negative = 0, 0
		res = Counter()
		# label_cnt = []

		for i, (gold_eid, probs) in enumerate(data): ## for each doc in testing data

			label_probs = sorted([(emotions[i],p) for i,p in enumerate(probs)], key=lambda x:x[1], reverse=True)




			
			

			## get gold answer
			gold_emotion = emotions[int(gold_eid)]

			## get prediction results
			if k == 'binary':
				## binary
				predict = [e for (e, p) in label_probs if p > 0.5]				
				# predict = [t[0] for t in results[i] if t[2] == True]
			else:
				## top1
				# predict = [t[0] for t in sorted(results[i], key=lambda x: float(x[1]), reverse=True )[:k]]
				predict = [e for (e, p) in label_probs][:k]

			really_is = Positive if target_emotion == gold_emotion else Negative
			classified_as = Positive if target_emotion in predict else Negative

			# print 'really_is:',really_is
			# print 'classified_as:',classified_as

			really_is_positive += 1 if really_is == Positive else 0
			really_is_negative += 1 if really_is == Negative else 0	
			

			TP = classified_as == Positive and really_is == Positive
			TN = classified_as == Negative and really_is == Negative
			FP = classified_as == Positive and really_is == Negative
			FN = classified_as == Negative and really_is == Positive


			res['TP'] += 1 if TP else 0
			res['TN'] += 1 if TN else 0
			res['FP'] += 1 if FP else 0
			res['FN'] += 1 if FN else 0		

		r = really_is_negative/float(really_is_positive)
		A = accuracy(res, ratio=r)

		Results['accuracy'].append((target_emotion, A))
	Results['avg_accuracy'] = round(sum(map(lambda x:x[1], Results['accuracy']))/float(len(Results['accuracy'])), 4)

	Results = dict(Results)
	Results['accuracy'] = dict(Results['accuracy'])

	return Results


if __name__ == '__main__':

	# eval_mdoc = evaluation(k=1)
	eval_mdoc = evaluation(fn='cache/fusion.csv', k='binary')
	find_intersection(eval_mdoc)



		
