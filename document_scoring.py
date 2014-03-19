import config, color
import pymongo,sys
from itertools import product

## for time
from collections import defaultdict
import time
from pprint import pprint


db = pymongo.Connection(config.mongo_addr)['LJ40K']

co_emotions = db[config.co_emotions_name]
co_docs = db[config.co_docs_name]
co_pats = db[config.co_pats_name]
co_lexicon = db[config.co_lexicon_name]
co_patscore = db[config.co_patscore_name]
co_docscore = db[config.co_docscore_name]

# create a local cache for event_scoring to reduce mongo access times
cache = {}

def significance_factor(pat):
	sf = config.sig_function_type
	if sf == 0: return 1
	elif sf == 1: return pat['pattern_length']
	elif sf == 2: return float(1)/pat['sent_length']
	elif sf == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )
	else: return False
	

miss = 0
hit = 0

def event_scoring(pat, emotion, cfg_patscore):

	
	query = { 'pattern': pat['pattern'].lower(), 'emotion': emotion, 'cfg': cfg_patscore }
	projector = { '_id': 0, 'score':1 }

	global cache, miss, hit
	# form key to access cache
	key = tuple([query[x] for x in sorted(query.keys())])

	# if key not in cache:
	# 	# fetch pattern score from mongo collection "patscore"
	# 	patscore_res = co_patscore.find_one( query, projector )
	# 	if not patscore_res:
	# 		cache[key] = -1
	# 		score_p_e = -1
	# 	else:
	# 		cache[key] = patscore_res['score']
	# 		score_p_e = patscore_res['score']
	# else:
	# 	score_p_e = cache[key]

	XX = time.time()
	patscore_res = co_patscore.find_one( query, projector )
	T['co_patscore.find_one'].append( time.time() - XX )



	XX = time.time()
	if key not in cache:
		miss += 1
		if not patscore_res:
			cache[key] = -1
		else:
			cache[key] = patscore_res['score']
	else:
		hit += 1
	score_p_e = cache[key]
	T['cache[key]'].append( time.time() - XX )

	## Total: 25.9145987034, Exec: 106120, Single: 0.000244200892418
	
	# patscore_res = co_patscore.find_one( query, projector )
	# score_p_e = -1 if not patscore_res else patscore_res['score']
	pat_weight = 1.0 if 'weight' not in pat else pat['weight']
	

	return pat_weight * significance_factor(pat) * score_p_e


## udocID=1000, emotion='happy'
## input: udocID, emotions to be tested, cfg for fetching pat scores
## output: a dictionary of emotion, doc_score
# {
# 	'happy': 0.2,
# 	'sad': 0.6,
# }
def document_scoring(udocID, emotions, cfg_patscore):
	## find all pats in the document <udocID>
	## Total: 0.0572915077209, Exec: 50, Single: 0.00114583015442
	# sfind_pats = time.time()
	pats = list( co_pats.find( {'udocID': udocID} ) )
	# T['find-pats-in-doc'].append( time.time() - sfind_pats )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats)),
		sys.stderr.flush()

	scores = {}
	for test_emotion in emotions:

		if config.verbose:
			print >> sys.stderr, '.',
			sys.stderr.flush()

		## calculate event scores
		## Total: 26.184949398, Exec: 2000, Single: 0.013092474699
		# ses = time.time()
		event_scores = filter( lambda x: x >=0, [ event_scoring(pat, test_emotion, cfg_patscore) for pat in pats ] )
		# T['cal-event-score-in-emotion'].append( time.time() - ses )

		## calculate documet scores
		## Total: 0.0136754512787, Exec: 2000, Single: 6.83772563934e-06	
		# sds = time.time()
		# arithmetic mean
		if config.ds_function_type == 0:
			doc_score = 0 if len(event_scores) == 0 else sum(event_scores) / float( len(event_scores) )
		# geometric mean
		elif config.ds_function_type == 1:
			doc_score = 0 if len(event_scores) == 0 else reduce(lambda x,y:x*y, event_scores )**(1/float(len(event_scores)))
		## undefined ds_function
		else:
			return False
		# T['cal-doc-score-in-emotion'].append( time.time() - sds )

		scores[test_emotion] = doc_score

	if config.verbose:
		print 
	return scores

T = defaultdict(list)

def update_all_document_scores(UPDATE=False):

	cfg_docscore = config.toStr(fields="ps_function,ds_function,sig_function,smoothing")
	cfg_patscore = config.toStr(fields="ps_function,smoothing")

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	_processed = 0

	for gold_emotion in emotions:

		# s = time.time()
		## get all document with emotions <gold_emotion> and ldocID is great than 800
		# Total: 0.000894069671631, Exec: 1, Single: 0.000894069671631
		docs = list( co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ) )
		# T['find-docs'].append( time.time() - s )

		if config.verbose:
			print >> sys.stderr, '%s ( %d docs )' % ( color.render(gold_emotion, 'g'), len(docs) )

		for doc in docs:

			_processed += 1
			if _processed <= 100: continue

			# score a document in 40 diff emotions
			## scoring a document: Total: 26.2910494804, Exec: 50, Single: 0.525820989609
			# stest_emotion = time.time()
			scores = document_scoring(doc['udocID'], emotions, cfg_patscore)
			# T['all-test-emotion'].append( time.time() - stest_emotion )


			# smongo = time.time()
			# save to mongo
			## Total: 0.0056939125061, Exec: 50, Single: 0.000113878250122
			if UPDATE:
				query = { 'udocID': doc['udocID'], 'gold_emotion': gold_emotion, 'cfg': cfg_docscore }
				update = { '$set': { 'scores': scores } }
				co_docscore.update(query, update, upsert=True)
			
			else:
				mdoc = { 'udocID': doc['udocID'], 'gold_emotion': gold_emotion, 'cfg': cfg_docscore, 'scores': scores }
				co_docscore.insert( mdoc )
			# T['save-mongo'].append( time.time() - smongo )

			

			# print 'processed %d/%d documents, current: udocID = %d' % (_processed, len(docs), doc['udocID'])
			
			if _processed == 150:
				for key in T:
					print key, '\t', 'Total:',sum(T[key]), '\t', 'Exec:', len(T[key]), '\t', 'Single:', sum(T[key])/float(len(T[key]))
				global miss, hit
				print '='*50
				print 'cache hit:',hit
				print 'cache miss:',hit
				print 'hit rate:',hit/float(hit+miss)

				exit(1)

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
			
	update_all_document_scores(UPDATE=False)

				
