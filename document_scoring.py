# -*- coding: utf-8 -*-
import config, color
import pymongo,sys
from itertools import product
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

## generate/fetch the patterns search list
def get_search_list():
	if config.min_count < 1: # 0, -1
		return False
	# check if the list existed
	# {
	# 	'limit': 1, # occur more than 1. i.e., drop all pattern with only 1 occurrence
	# 	'pats': [p1, ... pn]
	# }
	res = co_patsearch.find_one({'limit':config.min_count})
	if res:
		# use current list
		search_list = res['pats']
	else:
		# generate the list
		if config.verbose:
			print >> sys.stderr, 'cannot find limit search pattern list, re-generating...',
			sys.stderr.flush()

		C = Counter()
		for x in db['lexicon'].find(): C[x['pattern']] += x['count']
		mdoc = { 'limit': limit, 'pats': [] }
		for pat,count in sorted(C.items(), key=lambda x:x[1], reverse=True):
			if count <= limit: break
			mdoc['pats'].append(pat)

		# store in mongo
		db['pats_trim'].insert(mdoc)

		if config.verbose:
			print >> sys.stderr, 'done'

		search_list = mdoc['pats']

	return search_list

# create a local cache for event_scoring to reduce mongo access times
cache = {}

def significance_factor(pat):
	sf = config.sig_function_type
	if sf == 0: return 1
	elif sf == 1: return pat['pattern_length']
	elif sf == 2: return float(1)/pat['sent_length']
	elif sf == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )
	else: return False

def event_scoring(pat):

	query = { 'pattern': pat['pattern'].lower() }
	projector = { '_id': 0, 'scores':1 }

	global cache

	key = pat['pattern']

	if key not in cache:
		res = co_patscore.find_one( query, projector )

		if not res:
			cache[key] = {}
		else:
			cache[key] = res['scores']
	
	pat_scores = cache[key]
	
	return dict([(emotion, pat['weight'] * significance_factor(pat) * pat_scores[emotion]) for emotion in pat_scores])


## udocID=1000, emotion='happy'
## input: udocID, emotions to be tested, cfg for fetching pat scores
## output: a dictionary of emotion, doc_score
# {
# 	'happy': 0.2,
# 	'sad': 0.6,
# }
def document_scoring(udocID):
	# find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	D = defaultdict(list)
	
	# calculate the event score in each pattern
	for pat in pats:

		if pat['pattern'] not in search_list:
			continue

		EventScores = event_scoring(pat)
		for emotion in EventScores:
			D[emotion].append( EventScores[emotion] )
	
	scores = dict([(e, sum(D[e])/float(len(D[e])) ) for e in D])

	return scores

def update_all_document_scores(UPDATE=False):

	# cfg_docscore = config.getOpts(fields=config.opt_fields[config.ds_name], full=True)

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	_processed = 0

	search_list = get_search_list()

	for gold_emotion in emotions:

		## get all document with emotions <gold_emotion> and ldocID is great than 800
		docs = list( co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ) )

		if config.verbose:
			print >> sys.stderr, '%s ( %d docs )' % ( color.render(gold_emotion, 'g'), len(docs) )

		for doc in docs:

			# score a document in 40 diff emotions
			scores = document_scoring(doc['udocID'])
			mdoc = { 
				'udocID': doc['udocID'], 
				'gold_emotion': gold_emotion, 
				'scores': scores
			}
			co_docscore.insert( mdoc )

	# if config.verbose:
	# print '='*50
	# print 'cfg:',cfg_docscore

if __name__ == '__main__':
	  
	import getopt

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:g:s:l:vo',['help','ps_function=', 'ds_function=', 'sig_function=', 'smoothing=', 'limit=', 'verbose', 'overwirte'])
	except getopt.GetoptError:
		config.help(config.ds_name, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.ds_name)
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-d','--ds_function'): config.ds_function_type = int(arg.strip())
		elif opt in ('-g','--sig_function'): config.sig_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-l','--limit'): config.min_count = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwirte'): config.update = True

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_lexicon = db[config.co_lexicon_name]
	co_patsearch = db[config.co_patsearch_name]

	# get opts of ps_function, smoothing
	config.co_patscore_name = '_'.join([config.co_patscore_prefix] + config.getOpts(fields=config.opt_fields[config.ps_name], full=False))
	if config.co_patscore_name not in db.collection_names():
		print >> sys.stderr, '(error) source collection', color.render(config.co_patscore_name, 'yellow'),'is not existed'
		print >> sys.stderr, '\tcheck the fetch target and run again!!'
		exit(-1)

	co_patscore = db[ config.co_patscore_name ]

	# get opts of ps_function, ds_function, sig_function, smoothing
	# co_docscore_prefix and opts  --> e.g., docscore_d0_g3_p2_s1
	config.co_docscore_name = '_'.join([config.co_docscore_prefix] + config.getOpts(fields=config.opt_fields[config.ds_name], full=False))
	if config.co_docscore_name in db.collection_names():
		print >> sys.stderr, '(warning) destination collection', color.render(config.co_docscore_name, 'red'),'is already existed'
		print >> sys.stderr, '\t  use -o or --overwirte to force update'
		exit(-1)

	co_docscore = db[ config.co_docscore_name ]


	## confirm message
	_confirm_msg = [
		(config.ps_function_name, config.ps_function_type),
		(config.ds_function_name, config.ds_function_type),
		(config.sig_function_name, config.sig_function_type),
		(config.smoothing_name, config.smoothing_type),
		(config.limit_name, config.min_count),
		('fetch  collection', config.co_patscore_name),
		('insert  collection', config.co_docscore_name),
		('verbose', config.verbose),
		('overwirte', config.overwirte)
	]

	for k, v in _confirm_msg:
		print >> sys.stderr, k, ':', v
	print >> sys.stderr, '='*40
	print >> sys.stderr, 'press any key to start...', raw_input()
	

	## run
	import time
	s = time.time()
	update_all_document_scores(UPDATE=False)
	print 'Time total:',time.time() - s,'sec'

				
