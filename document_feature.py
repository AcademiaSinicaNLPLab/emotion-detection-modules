import config
import sys, pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

cache = {}

## input: pat
## output: a dictionary of (emotion, patscore)
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

## input: pat
## output: a dictionary of (emotion, patfeature) according to different featureValueType 
def get_patfeature(pattern):
	########################################################################################
	## type 0: pattern scores
	## type 1: accumulated threshold by 0.68 (1 standard diviation) using pattern scores
	## type 2: accumulated threshold by 0.68 (1 standard diviation) using pattern ocurrence
	########################################################################################

	if featureValueType == 0:
		patfeature = get_patscore(pattern) 

	elif featureValueType == 1:

		patscore = get_patscore(pattern)

		## temp_dict -> { 0.3: ['happy', 'angry'], 0.8: ['sleepy'], ... }
		temp_dict = defaultdict( list ) 
		for e in patscore:
			temp_dict[patscore[e]].append(e)

		## temp_list -> [ (0.8, ['sleepy']), (0.3, ['happy', 'angry']), ... ]
		temp_list = temp_dict.items()
		temp_list.sort(reverse=True)

		th = 0.68 * sum([patscore[k] for k in patscore])
		current_sum = 0
		selected_emotions = []
		while current_sum < th:
			top = temp_list.pop(0)
			selected_emotions.extend( top[1] )
			current_sum += top[0] * len(top[1])

		patfeature = dict( zip(selected_emotions, [1]*len(selected_emotions)) )

	# elif ...

	return patfeature


def get_document_feature(udocID):

	sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
	usentID_offset = min(sents)
	total_words = sum([sents[x] for x in sents])

	th1 = total_words * begPercentage/float(100)
	th2 = total_words * (begPercentage+midPercentage)/float(100)

	# print sents, '\ntotal_words = ', total_words, '\nusentID_offset = ', usentID_offset, '\nth1 = ', th1, '\nth2 = ', th2

	feature = Counter()

	## find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	for pat in pats:
		## find pattern position ( beginning/middle/end )
		lanchorID = sum([sents[usentID_offset+i] for i in range(pat['usentID'] - usentID_offset)]) + pat['anchor_idx']
		if lanchorID <= th1: position = 'beginning'
		elif lanchorID <= th2: position = 'middle'
		else: position = 'end'
		# print '='*30, '\n', pat['pattern'], '\n', 'lanchorID = ', lanchorID, '\n', 'position = ', position

		patfeature = get_patfeature(pat['pattern'])

		for e in patfeature: 
			key = '#position'+ '@'+ position + '_' + e
			feature[key] += patfeature[e]

	return feature

## old old old old old old version
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


def create_document_features():

	## insert metadata
	setting = { 
		"feature_type": "position", 
		"section": "b"+ str(begPercentage) + "_m" + str(midPercentage) + "_e" + str(endPercentage), 
		"counting_unit_type": countingUnitType, 
		"feature_value_type":countingUnitType 
	}
	setting_id = str(co_setting.insert( setting ))

	## list of emotions
	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	for (ie, gold_emotion) in enumerate(emotions):

		## get all document with emotions <gold_emotion> (ldocID: 0-799 for training, 800-999 for testing)
		docs = list( co_docs.find( { 'emotion': gold_emotion } ) )

		if config.verbose:
			print >> sys.stderr, '%d > %s ( %d docs )' % ( ie, color.render(gold_emotion, 'g'), len(docs) )

		for doc in docs:
			mdoc = {
				"emotion": gold_emotion,
				"udocID": doc['udocID'],
				"feature": get_document_feature(udocID=doc['udocID']).items(),
				"setting": setting_id # looks like "5369fb11d4388c0aa4c5ca4e"
			}
			co_feature.insert(mdoc)

	co_feature.create_index("setting")

if __name__ == '__main__':

	config.verbose = True

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_sents = db[config.co_sents_name]
	co_pats = db[config.co_pats_name]
	co_patscore = db['patscore_p2_s0']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.position']

	## parameters
	begPercentage=20
	midPercentage=60
	endPercentage=20
	countingUnitType=0
	featureValueType=1

	## run
	import time
	s = time.time()
	create_document_features()
	print 'Time total:',time.time() - s,'sec'
