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

from collections import defaultdict
T = defaultdict(list)
## udocID=1000, emotion='happy'
## ds_function=1, opt={'scoring': 1, 'smoothing': 0}, sig_function=0, epsilon=0.5
def document_scoring(udocID, emotion, ds_function, opt, sig_function, epsilon=0.5):

	s = time.time()
	mDocs = list( co_pats.find( {'udocID': udocID} ) ) 
	T['co_pats.find'].append(time.time()-s)

	
	# arithmetic mean
	if ds_function == 1:
		s = time.time()
		eventscores = filter( lambda x: x >=0, [event_scoring(pat, emotion, opt, sig_function) for pat in mDocs] )
		T['event_scoring'].append(time.time()-s)
		# all events not in lexicon
		if len(eventscores) == 0 : 
			return (None, 0)
		docscore = sum(eventscores) / float( len(eventscores) )
	# geometric mean
	elif ds_function == 2:
		docscore = reduce(lambda x,y:x*y, [event_scoring(pat, emotion, opt, sig_function) for pat in mDocs] )**(1/float(len(a)))
	## undefined ds_function
	else:
		return False
	return (docscore, 1) if docscore >= epsilon else (docscore, 0)

def event_scoring(pat, emotion, opt, sig_function):

	# build query
	query = {'pattern': pat['pattern'].lower(), 'emotion': emotion}
	query.update(opt)  # add entries in opt: scoring: 1, smoothing: 0
	
	# fetch pattern score from mongo collection "patscore"
	res = co_patscore.find_one( query )
	prob_p_e = -1 if not res else res['prob']
	
	return pat['weight'] * significance_factor(pat, sig_function) * prob_p_e


def significance_factor(pat, sig_function):
	if sig_function == 0: return 1
	if sig_function == 1: return pat['pattern_length']
	if sig_function == 2: return float(1)/pat['sent_length']
	if sig_function == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )


if __name__ == '__main__':

	ds_function = 1
	scoring = 1
	smoothing = 0
	opt = {'scoring': scoring, 'smoothing': smoothing}
	sig_function = 0
	epsilon = 0.5

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]
	# ts = {}
	for gold_emotion in emotions:	
		print gold_emotion
		docs = list(co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ))
		for doc in docs:
			_udocID = doc['udocID']
			for test_emotion in emotions:

				(doc_score, predict) = document_scoring(_udocID, test_emotion, ds_function, opt, sig_function, epsilon)

				query = {
						'udocID': _udocID,
						'gold_emotion': gold_emotion,
						'test_emotion': test_emotion,
						'ds_function': ds_function,
						'ps_function': scoring,
						'smoothing':  smoothing,
						'sig_function': sig_function,
						'epsilon':  epsilon,
				}
				u = {
						'$set': {
							'doc_score':  doc_score,
							'predict': predict
						}						
				}
				query.update(u)
				db['test'].insert(query)
		for k in T:
			print k, '\t', sum(T[k]), '\t', sum(T[k])/float(len(T[k]))
				# co_docscore.update(query, update, upsert=True)
