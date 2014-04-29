import config
import sys, pymongo, color

db = pymongo.Connection(config.mongo_addr)[config.db_name]


## input: pat (mongo document)
## output: a dictionary of emotion, pat_score
def get_patscore(pat):

	query = { 'pattern': pat['pattern'].lower() }
	projector = { '_id': 0, 'scores':1 }

	global cache

	key = pat['pattern']

	if key not in cache:
		res = co_patscore.find_one(query, projecter)
		if not res:
			cache[key] = {}
		else:
			cache[key] = res['scores']

	return cache[key]


def document_emotion_locations(udocID):
	# find total number of sents and usentID offset
	usentIDs = sorted( [ x['usentID'] for x in list( co_sents.find( {'udocID': udocID} ) ) ] )
	usentID_offset = usentIDs[0] - 1
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


def update_all_document_emotion_locations():

	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	for (ie, gold_emotion) in enumerate(emotions):
		## get all document with emotions <gold_emotion> and ldocID is great than 800
		docs = list( co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ) )

		if config.verbose:
			print >> sys.stderr, '%d > %s ( %d docs )' % ( ie, color.render(gold_emotion, 'g'), len(docs) )

		for doc in docs:
			locations = document_emotion_locations[doc['udocID']]
			mdoc = {
				'udocID': doc['udocID'],
				'locations': locations
			}
			co_location.insert(mdoc)


if __name__ == '__main__':
	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_sents = db[config.co_sents_name]
	co_pats = db[config.co_pats_name]
	co_patscore = db[]
	co_location = db[]

	## run
	import time
	s = time.time()
	update_all_document_emotion_locations()
	print 'Time total:',time.time() - s,'sec'

				
