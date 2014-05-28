import config
import sys, pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# global cache for pattern
cache = {}

# global cache for mongo.LJ40K.docs
mongo_docs = {}

# global cache for mongo.LJ40K.lexicon.pattern_total_count
PatTC = {}

## load entire mongo.LJ40K.docs into memory
def load_mongo_docs():
	global mongo_docs
	for mdoc in co_docs.find({}, {'_id':0}):
		udocID = mdoc['udocID']
		del mdoc['udocID']
		mongo_docs[udocID] = mdoc


##  PTC[33680]['i love you']
	#  340 
def load_lexicon_pattern_total_count():
	global PatTC
	for mdoc in db['lexicon.pattern_total_count'].find():
		PatTC[mdoc['udocID']] = {pat: count for pat, count in mdoc['pats']}


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

			new_score[mdoc['emotion']] = new_score[mdoc['emotion']] - PatTC[udocID][pattern.lower()]
			if new_score[mdoc['emotion']] == 0 :
				del new_score[mdoc['emotion']]

	return new_score


## input: dictionary of (emotion, value)
## output: dictionary of (emotion, 1) for emotions passed the threshold
def accumulate_threshold(score, percentage=0.68):
	## temp_dict -> { 0.3: ['happy', 'angry'], 0.8: ['sleepy'], ... }
	temp_dict = defaultdict( list ) 
	for e in score:
		temp_dict[score[e]].append(e)

	## temp_list -> [ (0.8, ['sleepy']), (0.3, ['happy', 'angry']), ... ] ((sorted))
	temp_list = temp_dict.items()
	temp_list.sort(reverse=True)

	th = percentage * sum([score[k] for k in score])
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

	score = get_patcount(pattern) # pattern count
	score = remove_self_count(udocID, pattern, score)
	if sum( [ score[e] for e in score ] ) < config.minCount: return {}

	## binary vector
	if config.featureValueType == 'b':
		return accumulate_threshold(score)
	
	## pattern count (frequency)
	elif config.featureValueType == 'f':
		if config.cut:
			binary_vector = accumulate_threshold(score)
			return { e: score[e] for e in binary_vector if binary_vector[e] == 1 }
		else:
			return score

	## pattern score
	elif config.featureValueType == 's':
		'''TODO'''		


def get_document_feature(udocID):

	sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
	usentID_offset = min(sents)
	total_words = sum([sents[x] for x in sents])

	th1 = total_words * config.begPercentage/float(100)
	th2 = total_words * (config.begPercentage+config.midPercentage)/float(100)

	# print sents, '\ntotal_words = ', total_words, '\nusentID_offset = ', usentID_offset, '\nth1 = ', th1, '\nth2 = ', th2

	docfeature = Counter()

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

		patfeature = get_patfeature(pat['pattern'], udocID)

		for e in patfeature: 
			key = '#position'+ '@'+ position + '_' + e
			docfeature[key] += patfeature[e]

	return docfeature


def create_document_features(setting_id):

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

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_sents = db[config.co_sents_name]
	co_pats = db[config.co_pats_name]
	co_nestedLexicon = db['lexicon.nested.min_count_4']
	co_patscore = db['patscore_p2_s0']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.pattern_emotion_position']

	## input arguments
	import getopt
	
	add_opts = [
		('-b', ['-b: percentage of beginning section (default: 20)']),
		('-m', ['-m: percentage of middle section (default: 60)']),
		('-e', ['-e: percentage of ending section (default: 20)']),
		('-f', ['-f: feature value type',
				'                 b: binary vector',
				'                 f: pattern count (frequency)',
				'                 s: pattern score']),
		('-n', ['-n: minimum count']),
		('--cut', ['--cut: cut off at accumulated count percentage = 68%'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hb:m:e:f:v',['help','begPercentage=', 'midPercentage=', 'endPercentage=', 'featureValueType=', 'verbose'])
	except getopt.GetoptError:
		config.help(config.patternEmotionPositionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.patternEmotionPositionFeat_name, addon=add_opts)
		elif opt in ('-b'): config.begPercentage = int(arg.strip())
		elif opt in ('-m'): config.midPercentage = int(arg.strip())
		elif opt in ('-e'): config.endPercentage = int(arg.strip())
		elif opt in ('-f'): config.featureValueType = arg.strip()
		elif opt in ('-n'): config.minCount = int( arg.strip() )
		elif opt in ('--cut'): config.cut = True
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "pattern_emotion_position", 
		"section": "b"+ str(config.begPercentage) + "_m" + str(config.midPercentage) + "_e" + str(config.endPercentage), 
		"feature_value_type": config.featureValueType,
		"min_count": config.minCount,
		"cut": config.cut
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## run
	load_mongo_docs()
	load_lexicon_pattern_total_count()
	create_document_features(setting_id)
