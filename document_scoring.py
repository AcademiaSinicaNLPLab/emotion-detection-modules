# -*- coding: utf-8 -*-
import config, color
import pymongo,sys
from itertools import product
from collections import defaultdict

db = pymongo.Connection(config.mongo_addr)['LJ40K']

# create a local cache for event_scoring to reduce mongo access times
cache, miss, hit = {}, 0, 0

def significance_factor(pat):
	sf = config.sig_function_type
	if sf == 0: return 1
	elif sf == 1: return pat['pattern_length']
	elif sf == 2: return float(1)/pat['sent_length']
	elif sf == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )
	else: return False
	
def event_scoring_old(pat, emotion, cfg_patscore):

	query = { 'pattern': pat['pattern'].lower(), 'emotion': emotion, 'cfg': cfg_patscore }
	projector = { '_id': 0, 'score':1 }

	global cache, miss, hit
	# form key to access cache
	key = tuple([query[x] for x in sorted(query.keys())])

	if key not in cache:
		miss += 1
		# fetch pattern score
		## co_patscore.find_one: Exec time: 0.000205091990844
		patscore_res = co_patscore.find_one( query, projector )
		if not patscore_res:
			cache[key] = -1
		else:
			cache[key] = patscore_res['score']
	else:
		hit += 1
	## cache[key]: Exec time: 1.81351154014e-06
	score_p_e = cache[key]
	pat_weight = 1.0 if 'weight' not in pat else pat['weight']
	
	return pat_weight * significance_factor(pat) * score_p_e

# ============================================================================================================ #

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
		EventScores = event_scoring(pat)
		for emotion in EventScores:
			D[emotion].append( EventScores[emotion] )

	# 
	scores = dict([(e, sum(D[e])/float(len(D[e])) ) for e in D])

	return scores

def update_all_document_scores(UPDATE=False):

	cfg_docscore = config.toStr(fields="ps_function,ds_function,sig_function,smoothing")
	# cfg_patscore = config.toStr(fields="ps_function,smoothing")

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	_processed = 0

	for gold_emotion in emotions:

		## get all document with emotions <gold_emotion> and ldocID is great than 800
		# Total: 0.000894069671631, Exec: 1, Single: 0.000894069671631
		docs = list( co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ) )

		if config.verbose:
			print >> sys.stderr, '%s ( %d docs )' % ( color.render(gold_emotion, 'g'), len(docs) )

		for doc in docs:

			# score a document in 40 diff emotions
			## scoring a document: Total: 26.2910494804, Exec: 50, Single: 0.525820989609
			scores = document_scoring(doc['udocID'])
			mdoc = { 'udocID': doc['udocID'], 'gold_emotion': gold_emotion, 'scores': scores }
			co_docscore.insert( mdoc )

	# if config.verbose:
	print '='*50
	print 'cfg:',cfg_docscore

if __name__ == '__main__':
	  
	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:g:s:v',['help','ps_function=', 'ds_function=', 'sig_function=', 'smoothing=', 'verbose'])
	except getopt.GetoptError:
		config.help('document_scoring', exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('document_scoring')
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-d','--ds_function'): config.ds_function_type = int(arg.strip())
		elif opt in ('-g','--sig_function'): config.sig_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_lexicon = db[config.co_lexicon_name]

	# get opts of ps_function, smoothing
	config.co_patscore_name = '_'.join([config.co_patscore_prefix] + config.getOpts(fields="p,s"))
	co_patscore = db[ config.co_patscore_name ]
	
	# get opts of ps_function, ds_function, sig_function, smoothing
	# co_docscore_prefix and opts  --> e.g., docscore_d0_g3_p2_s1
	config.co_docscore_name = '_'.join([config.co_docscore_prefix] + config.getOpts(fields="p,d,g,s"))
	co_docscore = db[ config.co_docscore_name ]	

	print >> sys.stderr, config.ps_function_name, '=', config.ps_function_type
	print >> sys.stderr, config.ds_function_name, '=', config.ds_function_type
	print >> sys.stderr, config.sig_function_name, '=', config.sig_function_type
	print >> sys.stderr, config.smoothing_name, '=', config.smoothing_type
	print >> sys.stderr, 'fetch  collection', '=', config.co_patscore_name
	print >> sys.stderr, 'insert collection', '=', config.co_docscore_name
	print >> sys.stderr, 'verbose =', config.verbose
	print >> sys.stderr, '='*40
	print >> sys.stderr, 'press any key to start...', raw_input()

	import time
	s = time.time()
	update_all_document_scores(UPDATE=False)
	print 'Time total:',time.time() - s,'sec'

				
