import config
import sys, pymongo
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

cache = {}

## input: pat
## output: a dictionary of emotion, pat_score
def get_patscore(pattern):

	query = { 'pattern': pattern.lower() }
	projector = { '_id': 0, 'scores':1 }

	global cache

	key = pattern

	if key not in cache:
		res = co_patscore.find_one(query, projector)
		if not res:
			cache[key] = {}
		else:
			cache[key] = res['scores']

	return cache[key]


def get_document_feature(udocID, beginning=20, middle=60, end=20):

	sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
	usentID_offset = min(sents) - 1
	total_words = sum([sents[x] for x in sents])

	th1 = total_words * float(beginning/100)
	th2 = total_words * float((beginning+middle)/100)

	feature = dict()
	feature['beginning'] = Counter()
	feature['middle'] = Counter()
	feature['end'] = Counter()

	## find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	for pat in pats:

		patscore = get_patscore(pat['pattern'])

		## find pattern location ( beginning->1, middle->2, end->3 )
		lanchorID = sum([sents[i] for i in range(pat['usentID'] - usentID_offset)]) + pat['anchor_idx']
		if lanchorID <= th1: position = 'beginning'
		elif lanchorID <= th2: position = 'middle'
		else: position = 'end'
		
		for e in patscore: 
			feature[position][e] += patscore[e]

	feature_vector = []
	for position in feature:
		feature_vector.extend( [feature[position][emotion] for emotion in emotions] )

	return feature_vector

## old version
def document_emotion_locations(udocID):
	# find total number of sents and usentID offset
	usentIDs = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
	usentID_offset = min(usentIDs) - 1
	number_of_sents = len(usentIDs)

	# find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )
	total_weight = 0

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	D = defaultdict(list)
	for pat in pats:
		pat_score = get_patscore(pat)
		if pat_score:
			total_weight += pat['weight']
		for emotion in pat_score:
			D[emotion].append( pat['weight'] * pat_score[emotion] *  pat['usentID'] )

	emotion_locations = dict([ ( e, (sum(D[e])/float(total_weight) - usentID_offset)/float(number_of_sents) ) for e in D ])
	return emotion_locations


def update_all_document_features():

	# for (ie, gold_emotion) in enumerate(emotions):
	ie = 0
	gold_emotion = emotions[0]

	## get all document with emotions <gold_emotion> and ldocID is great than 800
	docs = list( co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$lt': 3}} ) )

	if config.verbose:
		print >> sys.stderr, '%d > %s ( %d docs )' % ( ie, color.render(gold_emotion, 'g'), len(docs) )

	for doc in docs:
		mdoc = {
			'udocID': doc['udocID'],
			'emotion': gold_emotion,
			'feature': get_document_feature(doc['udocID'])
		}
		co_docfeature.insert(mdoc)


if __name__ == '__main__':

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_sents = db[config.co_sents_name]
	co_pats = db[config.co_pats_name]
	co_patscore = db['patscore_p2_s0']
	co_docfeature = db['docfeature_b20_m60_e20_c0_f0']

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]
	
	## run
	import time
	s = time.time()
	update_all_document_features()
	print 'Time total:',time.time() - s,'sec'

				
