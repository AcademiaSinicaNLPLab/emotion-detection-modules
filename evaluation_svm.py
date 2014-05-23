# -*- coding: utf-8 -*-
import config
import color
import re
import pymongo, sys, os
from collections import Counter, defaultdict
from itertools import product

from pprint import pprint

print >> sys.stderr, '[info] init ...',
sys.stderr.flush()
db = pymongo.Connection(config.mongo_addr)[config.db_name]
# get all emotions
emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])
eids = dict( enumerate(sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])) )
print >> sys.stderr, 'ok'

# setting_id = '537af6923681dff466c19e38'
# root = 'tmp'

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



# > svm.out
# {
# 	'setting': <str>,
# 	'param': <str>,
# 	'output': <list>
# }
# > svm.gold
# {
# 	'setting': <str>,
# 	'gold': <list>
# }

## load .gold.txt and .out from mongodb
def load_gold_out_from_mongo(setting_id, param):
	out_mdoc = co_svm_out.find_one({'setting': setting_id, 'param': param})
	gold_mdoc = co_svm_gold.find_one({'setting': setting_id})

	# generate <answer - predict> pair
	if out_mdoc and gold_mdoc:
		return zip(gold_mdoc['gold'], out_mdoc['out'])
	else:
		return False

## load .gold.txt and .out files
## and zip them together
def load_files(setting_id, param, root='tmp'):

	fn_gold = '.'.join([setting_id, 'gold', 'txt'])
	fn_out  = '.'.join([setting_id, param,  'out'])

	path_gold = os.path.join(root, fn_gold)
	path_out  = os.path.join(root, fn_out)

	list_gold = [line.strip().split('\t') for line in open(path_gold) if len(line.strip())]
	list_out = [int(line.strip()) for line in open(path_out) if len(line.strip())]

	# generate <answer - predict> pair
	pairs = zip([ int(x[0]) for x in list_gold], list_out)

	return pairs

def save_gold_out_to_mongo(setting_id, param, gold_out_paris):
	co_svm_gold.insert({'setting': setting_id, 'gold': [x[0] for x in gold_out_paris] })
	co_svm_gold.create_index('setting')

	co_svm_out.insert({'setting': setting_id, 'param': param, 'output': [x[1] for x in gold_out_paris] })
	co_svm_out.create_index([('setting', pymongo.ASCENDING), ('param', pymongo.ASCENDING)])


def load_eval_from_mongo(setting_id, param):
	eval_mdoc = co_svm_eval.find_one({'setting': setting_id, 'param': param})
	return False if not eval_mdoc else eval_mdoc

def save_eval_to_mongo(setting_id, param, results):
	eval_mdoc = {'setting': setting_id, 'param': param}
	for measure in ['accuracy', 'precision', 'recall', 'f1']:
		eval_mdoc[measure] = dict(Results[measure])
		eval_mdoc['avg_'+measure] = round(sum(map(lambda x:x[1], results[measure]))/float(len(results[measure])), 4)
	co_svm_eval.insert(eval_mdoc)
	co_svm_eval.create_index([('setting', pymongo.ASCENDING), ('param', pymongo.ASCENDING)])
	return eval_mdoc

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
	## results
	Results = defaultdict(list)

	for target_gold_id in eids:
		emotion = eids[target_gold_id]

		if config.verbose: 
			print >> sys.stderr, '>',emotion ,'...',
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

		r = really_is_negative/float(really_is_positive)

		A = accuracy(res, ratio=r)
		P = precision(res, ratio=r)
		R = recall(res, ratio=r)
		F = round(2*P*R/float(P+R), 4) if P+R > 0 else 0.0

		if config.verbose: print >> sys.stderr, A

		Results['accuracy'].append((emotion, A))
		Results['precision'].append((emotion, P))
		Results['recall'].append((emotion, R))
		Results['f1'].append((emotion, F))


	return Results

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

# eval_mdoc = {
#     setting: <str>, 		# setting_id
#     param: <str>,			# svm parameters
#
#     accuracy: <dict>,		# emotion -> accuracy 	-> score
#     precision: <dict>,	# emotion -> precision 	-> score
#     recall: <dict>,		# emotion -> recall 	-> score
#     f1: <dict>,			# emotion -> f1-score 	-> score
#
#     avg_accuracy: <float> # average accuracy
# }

def run(setting_id, param):
	if config.verbose: print >> sys.stderr, "[info] load eval mdoc from mongo"
	eval_mdoc = load_eval_from_mongo(setting_id, param)

	if not eval_mdoc:

		### (1) get paris
		if config.verbose: print >> sys.stderr, "[oops] can't find eval mdoc in mongo: to create one"
		if config.verbose: print >> sys.stderr, "[info] load gold/out pairs from mongo"
		pairs = load_gold_out_from_mongo(setting_id, param)
		
		if not pairs:

			if config.verbose: print >> sys.stderr, "[oops] can't find gold/out pairs in mongo: try local files"
			pairs = load_files(setting_id, param)

			
			if pairs:
				if config.verbose: print >> sys.stderr, "[info] got pairs from local files, save to mongo"
				save_gold_out_to_mongo(setting_id, param, gold_out_paris=pairs)
			else:
				print >> sys.stderr, "[error] can't load gold/out files"
				exit(-1)
		else:
			print >> sys.stderr, "[ok] <gold, out> pairs loaded"

		### (2) get results
		### send <gold,out> pairs to evaluate
		if config.verbose: print >> sys.stderr, "[info] start evaluating"
		Results = evaluate(pairs)

		### (3) get eval mdoc
		### save all results to mongo
		eval_mdoc = save_eval_to_mongo(setting_id, param, results=Results)
		if not eval_mdoc: 
			print >> sys.stderr, "[error] failed to save eval mdoc to mongo"
			exit(-1)

	if config.verbose: print >> sys.stderr, "[info] eval mdoc loaded"

	pprint(eval_mdoc)
if __name__ == '__main__':

	## default parameters
	setting_id = None
	root = 'tmp'
	param = 'default'
	update_all = False

	import getopt

	add_opts = [
		('--setting', 	['--setting: specify a setting ID (e.g., 537b00e33681df445d93d57e)', 
					   	 '           which can be retrieved from the mongo collection features.settings' ]),
		('--all', 		['-a, --all: evaluate and update all current experiments, default: '+str(update_all)+' )']), 
		('--param', 	['--param: parameter string for libsvm (e.g., use "b1c4", default: '+param+' )']),
		('--path', 		['-p, --path: path to local files (default: '+root+' )'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hva',['help', 'verbose', 'setting=', 'param=', 'all'])
	except getopt.GetoptError:
		config.help('run_svm', addon=add_opts, exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('run_svm', addon=add_opts)
		elif opt in ('-a','--all'): update_all = True
		elif opt in ('--param'): param = arg.strip()
		elif opt in ('-p','--path'): root = arg.strip()
		elif opt in ('--setting'): setting_id = arg.strip()
		elif opt in ('-v','--verbose'): config.verbose = True

	## select collections
	co_svm_eval = db[config.co_svm_eval_name]
	co_svm_out = db[config.co_svm_out_name]
	co_svm_gold = db[config.co_svm_gold_name]

	## check setting id
	if not setting_id:
		print >> sys.stderr, '[error] specify a setting id'
		exit(-1)
		# setting_ids = set([fn.split('.')[0] for fn in os.listdir(root) if re.match(r'^[0-9a-z]{24}', fn) ])
	else:
		setting_ids = [setting_id]

	## generate to do list
	if update_all:
		pass
	else:
		to_do_list = [(setting_id, param)]

	for (setting_id, param) in to_do_list:
		run(setting_id, param)




		
