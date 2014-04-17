# -*- coding: utf-8 -*-
import config
import pymongo, sys
from collections import Counter
from itertools import product

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# get all emotions
emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])

def fetch():

	config.co_docscore_name = '_'.join([config.co_docscore_prefix] + config.getOpts(fields="p,d,g,s"))

	if config.verbose:
		print >> sys.stderr, 'fetching doc scores from [', config.co_docscore_name, '] ...',
		sys.stderr.flush()

	co_docscore = db[ config.co_docscore_name ]
	co_docscore = db[ 'docscore_2_3_1' ]

	docs = list(co_docscore.find({}, {'_id':0}))

	if config.verbose:
		print >> sys.stderr, 'ok'

	return docs

def accuracy(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return round((TP+TN)/float(TP+TN+FN+FP), 4)

def precision(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return round((TP)/float(TP+FP), 4)

def recall(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return round((TP)/float(TP+FN), 4)

# target: happy
# really is Positive
# 	classify as happy	
#	classify as ~happy	
# really is Negative	
# 	classify as happy	
# 	classify as ~happy	

def evals(topk=1):

	Positive, Negative = True, False
	cfg = config.toStr(fields="ps_function,ds_function,sig_function,smoothing")

	# check if the collection already exists
	exist = len(list(db[config.co_results_name].find({'cfg': cfg }))) > 0

	# if exist: 
		# return True

	# get all instances
	insts = fetch()

	## ======================== start collecting Results ========================
	Results = {}
	for target_gold in emotions:

		really_is_positive, really_is_negative = 0, 0

		res = Counter()
		for inst in insts:

			### answers = [top-k emotions]
			answers = [x[0] for x in sorted(inst['scores'].items(), key=lambda x:x[1], reverse=True)][:topk]

			really_is = Positive if target_gold == inst['gold_emotion'] else Negative
			classified_as = Positive if target_gold in answers else Negative

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

		r = really_is_negative/float(really_is_positive)

		Results[target_gold] = {
			'res': res,
			'ratio': r
		}
	## ======================== end of collecting Results ========================

	mdoc = {
		'cfg': cfg, # use all options
		'emotions': {}
	}

	for target_gold in emotions:

		true_false_positive_negative = Results[target_gold]['res']
		r = Results[target_gold]['ratio']

		res = Results[target_gold]['res']

		A = accuracy(res, ratio=r)
		P = precision(res, ratio=r)
		R = recall(res, ratio=r)

		print A

		mdoc['emotions'][target_gold] = {
			'ratio': r, # /39
			'instances': true_false_positive_negative, # dict
			'accuracy': A,
			'precision': P,
			'recall': R,
			'f1': 2*P*R/float(P+R) if P+R > 0 else 0.0			
		}


	# db[config.co_results_name].insert( mdoc )

	return True


def average():
	
	LJ40K = [x['emotion'] for x in db['emotions'].find( { 'label': 'LJ40K' } )]
	Mishne05 = [x['emotion'] for x in db['emotions'].find( { 'label': 'Mishne05' } )]

	Union = set(LJ40K + Mishne05)

	results = db[config.co_results_name].find_one( {'cfg': config.toStr() } )


	res = results['emotions']
	print res

	print 'L\tM\tAccuracy\tEmotion'
	for e in Union:
		L = 'v' if e in LJ40K else 'x'
		M = 'v' if e in Mishne05 else 'x'
		A = '-' if e not in res else res[e]['accuracy']
		print L+'\t'+M+'\t'+str(A)+'\t'+e

	len_LJ40K = float(len([e for e in res if e in LJ40K]))
	len_Mishne05 = float(len([e for e in res if e in Mishne05]))

	sum_LJ40K = sum([res[e]['accuracy'] for e in res if e in LJ40K])
	sum_Mishne05 = sum([res[e]['accuracy'] for e in res if e in Mishne05])

	avg_LJ40K = sum_LJ40K/len_LJ40K

	avg_Mishne05 = sum_Mishne05/len_Mishne05


	# print avg_LJ40K, sum_LJ40K, len_LJ40K
	# print avg_Mishne05, sum_Mishne05, len_Mishne05

	
	shared_emotions = [x for x in Union if x in Mishne05 and x in LJ40K]

	avg_shared = sum([res[e]['accuracy'] for e in res if e in shared_emotions])/float(len([e for e in res if e in shared_emotions]))

	return avg_LJ40K, avg_Mishne05, avg_shared

if __name__ == '__main__':
	  
	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:g:s:v',['help','ps_function=', 'ds_function=', 'sig_function=', 'smoothing=', 'verbose'])
	except getopt.GetoptError:
		config.help('evaluation', exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('evaluation')
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-d','--ds_function'): config.ds_function_type = int(arg.strip())
		elif opt in ('-g','--sig_function'): config.sig_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	# if config.verbose:
	# 	print >> sys.stderr, 'evaluating...',
	# 	sys.stderr.flush()

	evals(topk=1)

	# if config.verbose:
		# print >> sys.stderr, 'ok'

	# print average()
