# -*- coding: utf-8 -*-
import config
import pymongo, sys
from collections import Counter
from itertools import product

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# get all emotions
emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])

def fetch():
	co_docscore = db[ config.co_docscore_name ]
	return list(co_docscore.find({}, {'_id':0}))

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

	for target_gold in emotions:

		res = Results[target_gold]['res']
		r = Results[target_gold]['ratio']

		query = { 
			'cfg': config.toStr(fields="ps_function,ds_function,sig_function,smoothing"), # use all options
			'emotion': target_gold
		}

		A = accuracy(res, ratio=r)
		P = precision(res, ratio=r)
		R = recall(res, ratio=r)

		upadte = { 
			'ratio': r, 
			'res': res,
			'accuracy': A,
			'precision': P,
			'recall': R,
			'f1': 2*P*R/float(P+R) if P+R > 0 else 0.0
		}

		db['results'].update( query, { '$set': upadte }, upsert=True )


def average(cfg):
	

	LJ40K = [x['emotion'] for x in db.emotions.find( { 'label': 'LJ40K' }, {'_id':0, 'emotion':1}  )]
	Mishne05 = [x['emotion'] for x in db.emotions.find( { 'label': 'Mishne05' }, {'_id':0, 'emotion':1}  )]

	results = list(db['results'].find( cfg ))

	mdocs = [x for x in results if x['emotion'] in LJ40K]
	avg_LJ40K = sum([x['accuracy'] for x in mdocs])/float(len(mdocs))

	mdocs = [x for x in results if x['emotion'] in Mishne05]
	avg_Mishne05 = sum([x['accuracy'] for x in mdocs])/float(len(mdocs))

	U = set(LJ40K + Mishne05)
	shared_emotions = [x for x in U if x in Mishne05 and x in LJ40K]

	mdocs = [x for x in results if x['emotion'] in shared_emotions]
	avg_shared = sum([x['accuracy'] for x in mdocs])/float(len(mdocs))

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

	print >> sys.stderr, config.ps_function_name, '=', config.ps_function_type
	print >> sys.stderr, config.ds_function_name, '=', config.ds_function_type
	print >> sys.stderr, config.sig_function_name, '=', config.sig_function_type
	print >> sys.stderr, config.smoothing_name, '=', config.smoothing_type
	print >> sys.stderr, 'fetch  collection', '=', config.co_patscore_name
	print >> sys.stderr, 'insert collection', '=', config.co_docscore_name
	print >> sys.stderr, 'verbose =', config.verbose
	print >> sys.stderr, '='*40
	print >> sys.stderr, 'press any key to start...', raw_input()

	evals(topk=1)

# if __name__ == '__main__':

# 	ps_functions = [2]
# 	sig_functions = [3]
# 	smoothing = 1



# 	for ps_function, sig_function in list(product(ps_functions, sig_functions)):
# 		print 'update',ps_function, sig_function
# 		evals(ps_function, sig_function, smoothing, topk=1)

	# average(cfg)


	

