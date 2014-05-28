import config
import sys, pymongo, color, os, pickle
from collections import defaultdict, Counter
from pprint import pprint

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# global cache for pattern
cache = {}

# global cache for mongo.LJ40K.docs
mongo_docs = {}

# global cache for mongo.LJ40K.lexicon.pattern_total_count
PatTC = {}

## load entire mongo.LJ40K.docs into memory
def load_mongo_docs():
	if not os.path.exists('cache/mongo_docs.pkl'):
		if not os.path.exists('cache'): os.mkdir('cache')
		for mdoc in co_docs.find({}, {'_id':0}):
			udocID = mdoc['udocID']
			del mdoc['udocID']
			mongo_docs[udocID] = mdoc
		pickle.dump(mongo_docs, open('cache/mongo_docs.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		mongo_docs = pickle.load(open('cache/mongo_docs.pkl','rb'))
	return mongo_docs



##  PTC[33680]['i love you']
#  340 
def load_lexicon_pattern_total_count():
	global PatTC
	exists = os.path.exists('PTC.lexicon.pkl')
	if not exists:
		for mdoc in db['lexicon.pattern_total_count'].find():
			PatTC[mdoc['udocID']] = {pat: count for pat, count in mdoc['pats']}
		pickle.dump(PatTC, open('PTC.lexicon.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		PatTC = pickle.load(open('PTC.lexicon.pkl','rb'), protocol=pickle.HIGHEST_PROTOCOL)


## input: pattern
## output: a dictionary of (emotion, patscore)
def get_patscore(pattern):

	global cache

	if pattern not in cache:
		
		query = { 'pattern': pattern.lower() }
		projector = { '_id': 0, 'scores':1 }
		res = co_patscore.find_one(query, projector)
		
		if not res:
			cache[pattern] = {}
		else:
			cache[pattern] = res['scores']

	return cache[pattern]


## input: pattern
## output: a dictionary of (emotion, occurrence)
def get_patcount(pattern):

	global cache

	if pattern not in cache:

		query = { 'pattern': pattern.lower() }
		projector = { '_id': 0, 'count':1 }
		res = co_nestedLexicon.find_one(query, projector)

		if not res:
			cache[pattern] = {}
		else:
			cache[pattern] = res['count']

	return cache[pattern]


## input: dictionary of (emotion, count)
## output: dictionary of (emotion, count)
def remove_self_count(udocID, pattern, score_dict):

	global mongo_docs
	mdoc = mongo_docs[udocID] # use pre-loaded

	new_score = dict(score_dict)

	if new_score: 

		## ldocID: 0-799	
		if mdoc['ldocID'] < 800: 

			# new_score[mdoc['emotion']] = new_score[mdoc['emotion']] - PatTC[udocID][pattern.lower()]
			# new_score[mdoc['emotion']] = new_score[mdoc['emotion']]
			if new_score[mdoc['emotion']] == 0 :
				del new_score[mdoc['emotion']]

	return new_score


## input: dictionary of (emotion, value)
## output: dictionary of (emotion, 1) for emotions passed the threshold
def accumulate_threshold(score, percentage):
	## temp_dict -> { 0.3: ['happy', 'angry'], 0.8: ['sleepy'], ... }
	## (count)	    { 2:   ['bouncy', 'sleepy', 'hungry', 'creative'], 3: ['cheerful']}
	temp_dict = defaultdict( list ) 
	for e in score:
		temp_dict[score[e]].append(e)
	
	## temp_list -> [ (0.8, ['sleepy']), (0.3, ['happy', 'angry']), ... ] ((sorted))
	## (count)	    [ (3, ['cheerful']), (2,   ['bouncy', 'sleepy', 'hungry', 'creative'])]
	temp_list = temp_dict.items()
	temp_list.sort(reverse=True)

	th = percentage * sum( score.values() )
	current_sum = 0
	selected_emotions = []

	while current_sum < th:
		top = temp_list.pop(0)
		selected_emotions.extend( top[1] )
		current_sum += top[0] * len(top[1])

	return dict( zip(selected_emotions, [1]*len(selected_emotions)) )


## output: a dictionary of (emotion, patfeature) according to different featureValueType 
def get_patfeature(pattern, udocID):
	########################################################################################
	## [Options]
	## 		config.minCount
	## 		config.featureValueType
	## 		config.cut
	########################################################################################

	# score <dict> emotion --> patcount
	# {
	#	'aggravated': 3,
	#  	'amused': 2,
	#  	'anxious': 3, ...
	# }
	score = get_patcount(pattern) # pattern count

	if not score: return {}

	# score = remove_self_count(udocID, pattern, score)

	# check if total patcount < min_count
	if sum( score.values() ) < config.minCount: return {}
	
	percentage = config.cutoffPercentage/float(100)

	## binary vector
	if config.featureValueType == 'b':
		return accumulate_threshold(score, percentage)
	
	## pattern count (frequency)
	elif config.featureValueType == 'f':
		if config.cut:
			binary_vector = accumulate_threshold(score, percentage)
			return { e: score[e] for e in binary_vector if binary_vector[e] == 1 }
		else:
			return score

	## pattern score
	elif config.featureValueType == 's':
		'''TODO'''
		return None
	else:
		return False
	


def get_document_feature(udocID):

	docfeature = Counter()

	## find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	for pat in pats:

		patfeature = get_patfeature(pat['pattern'], udocID)

		for e in patfeature: 
			docfeature[e] += patfeature[e]

	return docfeature


def create_document_features():

	## list of emotions
	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	for (ie, gold_emotion) in enumerate(emotions):

		## get all document with emotions <gold_emotion> (ldocID: 0-799 for training, 800-999 for testing)
		docs = list( co_docs.find( { 'emotion': gold_emotion } ) )

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

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_sents = db[config.co_sents_name]
	co_pats = db[config.co_pats_name]
	co_nestedLexicon = db['lexicon.nested.pruned']
	co_patscore = db['patscore_p2_s0']

	## target mongo collections
	co_setting = db['debug.features.settings']
	co_feature = db['debug.features.pattern_emotion']

	## input arguments
	import getopt
	
	add_opts = [
		('-f', ['-f: feature value type',
				'                 b: binary vector',
				'                 f: pattern count (frequency)',
				'                 s: pattern score']),
		('-n', ['-n: filter out patterns with minimum count',
			    '                 k: minimum count']),
		('-c', ['-c: cut off by accumulated count percentage',
				'                 k: cut at k%'])		
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hf:n:c:v',['help', 'featureValueType=', 'minCount=', 'cut', 'verbose'])
	except getopt.GetoptError:
		config.help(config.patternEmotionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.patternEmotionFeat_name, addon=add_opts)
		elif opt in ('-f'): config.featureValueType = arg.strip()
		elif opt in ('-n'): config.minCount = int( arg.strip() )
		elif opt in ('-c'): config.cutoffPercentage = int( arg.strip() )
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "pattern_emotion", 
		"feature_value_type": config.featureValueType,
		"min_count": config.minCount,
		"cutoff_percentage": config.cutoffPercentage
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## run
	print 'load_mongo_docs'
	mongo_docs = load_mongo_docs()
	# print 'load_lexicon_pattern_total_count'
	# load_lexicon_pattern_total_count()
	print 'create_document_features'
	create_document_features()
