import config
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
	if config.sig_function == 0: return 1
	elif config.sig_function == 1: return pat['pattern_length']
	elif config.sig_function == 2: return float(1)/pat['sent_length']
	elif config.sig_function == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )
	else: return False
	



def event_scoring(pat, emotion, cfg_patscore):

	# global cache
	query = { 'pattern': pat['pattern'].lower(), 'emotion': emotion, 'cfg': cfg_patscore }
	
	# # form key to access cache
	# key = tuple([query[x] for x in sorted(query.keys())])

	# if key not in cache:
	# 	# fetch pattern score from mongo collection "patscore"
	# 	res = co_patscore.find_one( query )
	# 	if not res:
	# 		cache[key] = -1
	# 	else:
	# 		cache[key] = res['prob']
	# score_p_e = cache[key]

	patscore_res = co_patscore.find_one( query )
	score_p_e if not patscore_res else patscore_res['score']

	pat_weight = 1.0 if 'weight' not in pat else pat['weight']

	return pat_weight * significance_factor(pat) * score_p_e


## udocID=1000, emotion='happy'
## ds_function=1, opt={'scoring': 1, 'smoothing': 0}, sig_function=0, epsilon=0.5
def document_scoring(udocID, emotion):

	## find all pats in the document <udocID>
	# avg: 0.0008 sec 
	mDocs = list( co_pats.find( {'udocID': udocID} ) )

	## calculate event scores
	event_scores = filter( lambda x: x >=0, [ event_scoring(pat, emotion, cfg_patscore) for pat in mDocs ] )

	# [ event_scoring(pat, emotion, cfg_patscore) for pat in mDocs ]

	# arithmetic mean
	if config.ds_function_type == 0:

		doc_score = 0 if len(event_scores) == 0 else sum(event_scores) / float( len(event_scores) )

	# geometric mean
	elif config.ds_function_type == 1:

		doc_score = 0 if len(event_scores) == 0 else reduce(lambda x,y:x*y, event_scores )**(1/float(len(event_scores)))

	## undefined ds_function
	else:
		return False

	return doc_score

def update_all_document_scores(UPDATE=False, DEBUG=False):

	cfg_docscore = config.toStr(fields="ps_function,ds_function,sig_function,smoothing")
	cfg_patscore = config.toStr(fields="ps_function,smoothing")

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	for gold_emotion in emotions:

		## get all document with emotions <gold_emotion> and ldocID is great than 800
		docs = list( co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ) )

		for doc in docs:

			# {
			# 	'udocID': udocID,
			# 	'gold_emotion': gold_emotion,
			#	'cfg': "",
			# 	'scores' : 
			# 	{
			# 		'happy': 0.67,
			# 		'sad': ...,
			# 		...
			# 	}	
			# }

			scores = {}

			# score a document in 40 diff emotions
			for test_emotion in emotions:
				doc_score = document_scoring(doc['udocID'], test_emotion)
				scores[test_emotion] = doc_score


			if UPDATE:

				query = { 'udocID': doc['udocID'], 'gold_emotion': gold_emotion, 'cfg': cfg_docscore }
				update = { '$set': { 'scores': scores } }
				co_docscore.update(query, update, upsert=True)
			
			else:
				mdoc = { 'udocID': doc['udocID'], 'gold_emotion': gold_emotion, 'cfg': cfg_docscore, 'scores': scores }
				co_docscore.update( mdoc )



if __name__ == '__main__':
	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:g:s:v',['help','ps_function=', 'ds_function=', 'sig_function=', 'smoothing=', 'verbose'])
	except getopt.GetoptError:
		config.help('document_scoring', exit=2)

	verbose = False
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('document_scoring')
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-d','--ds_function'): config.ds_function_type = int(arg.strip())
		elif opt in ('-g','--sig_function'): config.sig_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-v','--verbose'): verbose = True
			


				
