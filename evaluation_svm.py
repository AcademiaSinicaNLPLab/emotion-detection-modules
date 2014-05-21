# -*- coding: utf-8 -*-
import config
import color
import pymongo, sys, os
from collections import Counter
from itertools import product

db = pymongo.Connection(config.mongo_addr)[config.db_name]

setting_id = '537af6923681dff466c19e38'
root = 'tmp'

def accuracy(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return 0.0 if TP+TN+FN+FP == 0 else round((TP+TN)/float(TP+TN+FN+FP), 4)

def precision(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return 0.0 if TP+FP == 0 else round((TP)/float(TP+FP), 4)

def recall(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return 0.0 if TP+FN == 0 else round((TP)/float(TP+FN), 4)


# get all emotions
emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])

eids = dict( enumerate(sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])) )


def load_files(setting_id, root='tmp', param='default'):

	fn_gold = '.'.join([setting_id, 'gold', 'txt'])
	fn_out  = '.'.join([setting_id, param,  'out'])

	path_gold = os.path.join(root, fn_gold)
	path_out  = os.path.join(root, fn_out)

	list_gold = [line.strip().split('\t') for line in open(path_gold) if len(line.strip())]
	list_out = [int(line.strip()) for line in open(path_out) if len(line.strip())]

	# print a
	# print p
	# raw_input()

	# generate <answer - predict> pair
	pairs = zip([ int(x[0]) for x in list_gold], list_out)

	# # print pairs
	# w = [(x,y) for (x,y) in pairs if x == y]
	# print w
	# print len(w)

	## make sure the eid is in the default assending order
	## i.e., 0:accomplished, 1:aggravated, ..., 39:tired
	## just in case the order has been changed in the previous stage
	# global eids
	# eids = dict([( int(x[0]) , x[2]) for x in list_gold])
	# print eids
	return pairs


# target: happy
# really is Positive
# 	classify as happy	
#	classify as ~happy	
# really is Negative	
# 	classify as happy	
# 	classify as ~happy

def evaluate(pairs):
	global eids
	Positive, Negative = True, False
	As = []

	for target_gold_id in eids:
		# print >> sys.stderr, '>',eids[target_gold_id] ,'...',
		sys.stderr.flush()

		really_is_positive, really_is_negative = 0, 0
		res = Counter()

		ri, rn = 0, 0

		for pair in pairs:

			predict_answers = [ pair[1] ]

			really_is = Positive if target_gold_id == pair[0] else Negative
			classified_as = Positive if target_gold_id in predict_answers else Negative

			## stat really_is_Positive: really_is_Negative = 200: 7900
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

		# print eids[target_gold_id]
		# print '\t', res

		r = really_is_negative/float(really_is_positive)

		A = accuracy(res, ratio=r)
		P = precision(res, ratio=r)
		R = recall(res, ratio=r)

		# print >> sys.stderr, 'done'

		# print '\taccu', A
		# print '\tprec', P
		# print '\trecall', R
		# print '\tf1', 2*P*R/float(P+R) if P+R > 0 else 0.0
		# print 
		# raw_input()
		print eids[target_gold_id], '\t', A
		As.append(A)

	return As

	# print sum(As)/float(len(As))


def average():
	LJ40K = [x['emotion'] for x in db['emotions'].find( { 'label': 'LJ40K' } )]
	Mishne05 = [x['emotion'] for x in db['emotions'].find( { 'label': 'Mishne05' } )]
	Union = set(LJ40K + Mishne05)

	results = co_results.find_one( {'cfg': cfg } )

	res = results['emotions']

	print >> sys.stdout, 'L\tM\tAccu.\tEmotion'
	print >> sys.stdout, '='*40

	for e in Union:
		L = 'v' if e in LJ40K else 'x'
		M = 'v' if e in Mishne05 else 'x'
		A = '-' if e not in res else res[e]['accuracy']
		print >> sys.stdout, L+'\t'+M+'\t'+str(A)+'\t'+e

	len_LJ40K = float(len([e for e in res if e in LJ40K]))
	len_Mishne05 = float(len([e for e in res if e in Mishne05]))

	sum_LJ40K = sum([res[e]['accuracy'] for e in res if e in LJ40K])
	sum_Mishne05 = sum([res[e]['accuracy'] for e in res if e in Mishne05])

	avg_LJ40K = sum_LJ40K/len_LJ40K
	avg_Mishne05 = sum_Mishne05/len_Mishne05
	
	shared_emotions = [x for x in Union if x in Mishne05 and x in LJ40K]
	avg_shared = sum([res[e]['accuracy'] for e in res if e in shared_emotions])/float(len([e for e in res if e in shared_emotions]))

	print >> sys.stdout, '='*40
	print >> sys.stdout, 'Avg. LJ40K:', round(avg_LJ40K,4)
	print >> sys.stdout, 'Avg. Mishne05:', round(avg_Mishne05,4)
	print >> sys.stdout, 'Avg. Overall:', round(avg_shared,4)
	# print >> sys.stderr, avg_LJ40K, avg_Mishne05, avg_shared

	return avg_LJ40K, avg_Mishne05, avg_shared

if __name__ == '__main__':

	import re

	setting_id = '537b00e33681df445d93d57e'
	# setting_id = None
	# ids = 
	root = 'tmp'
	svm_param = 'c9'

	if not setting_id:

		setting_ids = set([fn.split('.')[0] for fn in os.listdir(root) if re.match(r'^[0-9a-z]{24}', fn) ])
	else:
		setting_ids = [setting_id]

	for setting_id in setting_ids:


		pairs = load_files(setting_id, param=svm_param)
		As = evaluate(pairs)
		# print As
		print >> sys.stderr, setting_id, '\t', sum(As)/float(len(As))
		# raw_input()	



	# working_root = '/Users/Maxis/projects/emotion-detection-modules/data/'


	# print pairs



