import pymongo
from itertools import product

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
co_emotions = db['emotions']
co_docs = db['docs']
co_pats = db['pats']
co_lexicon = db['lexicon']
co_patscore = db['patscore']
co_docscore = db['docscore']

# create a local cache for event_scoring to reduce mongo access times
cache = {}

## udocID=1000, emotion='happy'
## ds_function=1, opt={'scoring': 1, 'smoothing': 0}, sig_function=0, epsilon=0.5
def document_scoring(udocID, emotion, ds_function, opt, sig_function, epsilon=0.5):

	# avg: 0.0008 sec 
	mDocs = list( co_pats.find( {'udocID': udocID} ) )

	# arithmetic mean
	if ds_function == 1:
		eventscores = filter( lambda x: x >=0, [ event_scoring(pat, emotion, opt, sig_function) for pat in mDocs ] )
		# all events not in lexicon
		if len(eventscores) == 0 : 
			return (None, 0)
		docscore = sum(eventscores) / float( len(eventscores) )

	# geometric mean
	elif ds_function == 2:
		docscore = reduce(lambda x,y:x*y, [ event_scoring(pat, emotion, opt, sig_function) for pat in mDocs ] )**(1/float(len(a)))
	## undefined ds_function
	else:
		return False
	return (docscore, 1) if docscore >= epsilon else (docscore, 0)


def event_scoring(pat, emotion, opt, sig_function):

	global cache

	query = {'pattern': pat['pattern'].lower(), 'emotion': emotion}
	query.update(opt)  # add entries in opt: scoring: 1, smoothing: 0
	
	# form key to access cache
	key = tuple([query[x] for x in sorted(query.keys())])

	if key not in cache:
		# fetch pattern score from mongo collection "patscore"
		res = co_patscore.find_one( query )
		if not res:
			cache[key] = -1
		else:
			cache[key] = res['prob']

	prob_p_e = cache[key]
	
	return pat['weight'] * significance_factor(pat, sig_function) * prob_p_e


def significance_factor(pat, sig_function):
	if sig_function == 0: return 1
	if sig_function == 1: return pat['pattern_length']
	if sig_function == 2: return float(1)/pat['sent_length']
	if sig_function == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )


if __name__ == '__main__':


	overwrite = False

	ds_function = 1
	scoring = 1
	smoothing = 0
	opt = {'scoring': scoring, 'smoothing': smoothing}
	sig_function = 0
	epsilon = 0.5

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]
	for gold_emotion in emotions:

		print gold_emotion
		for doc in co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ):
			_udocID = doc['udocID']
			for test_emotion in emotions:

				Q = {
						'udocID': _udocID,
						'gold_emotion': gold_emotion,
						'test_emotion': test_emotion,
						'ds_function': ds_function,
						'ps_function': scoring,
						'smoothing':  smoothing,
						'sig_function': sig_function,
						'epsilon':  epsilon,
				}
				
				if not overwrite:
					# check if exist
					res = co_docscore.find_one(Q)
					if res:
						# value already exists, don't do update nor insert
						continue
				
				(doc_score, predict) = document_scoring(_udocID, test_emotion, ds_function, opt, sig_function, epsilon)

				U = {
						'doc_score':  doc_score,
						'predict': predict						
				}
				update = { '$set': U }

				# Avg: 0.000098 sec
				# query_for_insert = dict(Q.items() + U.items())
				# co_docscore.insert(query_for_insert)

				co_docscore.update(Q, update, upsert=True)
				
