# -*- coding: utf-8 -*-
import config
import color
import pymongo, sys
from collections import Counter
from itertools import product

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# get all emotions
emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])

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

def evals():

	Positive, Negative = True, False

	# fetch all instances
	## ======================== start fetch instances ===========================
	print >> sys.stderr, 'fetching from', config.co_docscore_name, '...',
	sys.stderr.flush()
	insts = list(co_docscore.find({}, {'_id':0}))
	print >> sys.stderr, 'done (get',len(insts),'instances )'
	## ======================== end fetch instances =============================

	## ======================== start collecting Results ========================
	Results = {}
	for target_gold in emotions:
		if config.verbose:
			print >> sys.stderr, 'evaluating',target_gold ,'...',
			sys.stderr.flush()

		really_is_positive, really_is_negative = 0, 0

		res = Counter()
		for inst in insts:

			### answers = [top-k emotions]
			answers = [x[0] for x in sorted(inst['scores'].items(), key=lambda x:x[1], reverse=True)][:config.topk]

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
		if config.verbose:
			print >> sys.stderr, 'ok'
	## ======================== end of collecting Results =======================

	mdoc = {
		'cfg': cfg, # use all options
		'emotions': {} # emotion: { happy: {...}, sad: {...}, }
	}
	# forming mongo document
	for target_gold in emotions:

		true_false_positive_negative = Results[target_gold]['res']
		r = Results[target_gold]['ratio']
		res = Results[target_gold]['res']

		A = accuracy(res, ratio=r)
		P = precision(res, ratio=r)
		R = recall(res, ratio=r)

		mdoc['emotions'][target_gold] = {
			'ratio': r, # /39
			'instances': true_false_positive_negative, # dict
			'accuracy': A,
			'precision': P,
			'recall': R,
			'f1': 2*P*R/float(P+R) if P+R > 0 else 0.0			
		}

	# if config.overwrite:
	print >> sys.stderr, 'upsert mongo document', cfg
	co_results.update({'cfg': cfg}, {'$set': {'emotions':mdoc['emotions']}}, upsert=True )


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
	  
	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:g:s:l:vo',['help','ps_function=', 'ds_function=', 'sig_function=', 'smoothing=', 'limit=', 'verbose', 'overwrite'])
	except getopt.GetoptError:
		config.help('evaluation', exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('evaluation')
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-d','--ds_function'): config.ds_function_type = int(arg.strip())
		elif opt in ('-g','--sig_function'): config.sig_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-l','--limit'): config.min_count = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True

	## fetch from collection
	config.co_docscore_name = '_'.join([config.co_docscore_prefix] + config.getOpts(fields=config.opt_fields[config.ev_name], full=False))

	# if cannot find the fetch target collection
	co_docscore_existed = config.co_docscore_name in db.collection_names()
	if not co_docscore_existed:
		print >> sys.stderr, '(error) collection', color.render(config.co_docscore_name, 'yellow'),'is not existed'
		print >> sys.stderr, '\tcheck the fetch target and run again!!'
		exit(-1)

	# check if the collection already exists
	cfg = ','.join(config.getOpts(fields=config.opt_fields[config.ev_name], key_value='=', full=True))
	mdoc_results_existed = True if db[config.co_results_name].find_one( {'cfg': cfg} ) else False
	skip_eval = False if not mdoc_results_existed or config.overwrite else True

	co_docscore = db[ config.co_docscore_name ]
	co_results = db[ config.co_results_name ]

	## confirm message
	confirm_msg = [
		(config.ps_function_name, config.ps_function_type),
		(config.ds_function_name, config.ds_function_type),
		(config.sig_function_name, config.sig_function_type),
		(config.limit_name, config.min_count),
		('fetch collection', config.co_docscore_name, '(existed)' if co_docscore_existed else '(none)'),
		('insert collection', config.co_results_name, '(existed)' if mdoc_results_existed else '(none)'),
		('verbose', config.verbose),
		('overwrite', config.overwrite, { True: color.render('!Note: This will drop the collection [ '+config.co_docscore_name+' ]' if co_docscore_existed else '', 'red'), False: '' })
	]


	config.print_confirm(confirm_msg, bar=40, halt=True if not skip_eval else False)


	if skip_eval:
		## (warning) destination's already existed
		print >> sys.stderr, '(warning) destination mongo doc', color.render(config.co_results_name+' > '+cfg, 'red'),'is already existed'
		print >> sys.stderr, '\t  use -o or --overwrite to force update'

	if not skip_eval:
		evals()

	if skip_eval:
		average()
