import config
import sys, pymongo, color, os, pickle
from collections import defaultdict, Counter
from pprint import pprint
import logging
import util
# from util import load_lexicon_pattern_total_count
import lexicon_total_count
db = pymongo.Connection(config.mongo_addr)[config.db_name]

# global cache for pattern
cache = {}

# global cache for mongo.LJ40K.docs
mongo_docs = {}

# global cache for mongo.LJ40K.lexicon.pattern_total_count
PatTC = {}

remove_type = '0'


## input: pattern
## output: a dictionary of (emotion, occurrence)
def get_patcount(pattern):

	global cache

	if pattern not in cache:

		query = { 'pattern': pattern.lower() }
		projector = { '_id': 0, 'count':1 }
		res = co_lexicon.find_one(query, projector)

		if not res:
			cache[pattern] = {}
		else:
			cache[pattern] = res['count']

	return cache[pattern]


## input: dictionary of (emotion, count)
## output: dictionary of (emotion, count)
def remove_self_count(udocID, pattern, count_dict, category, condition=False):

	global mongo_docs
	mdoc = mongo_docs[udocID] # use pre-loaded

	new_count = dict(count_dict)

	if new_count: 

		## ldocID: 0-799
		if condition: ## for LJ40K, identify training
			if mdoc['ldocID'] < 800:
				new_count[mdoc[category]] = new_count[mdoc[category]] - PatTC[udocID][pattern.lower()]
		else:
			## all are considering as training
			new_count[mdoc[category]] = new_count[mdoc[category]] - PatTC[udocID][pattern.lower()]

			# new_count[mdoc['emotion']] = new_count[mdoc['emotion']]
			if new_count[mdoc[category]] == 0 :
				del new_count[mdoc[category]]

	return new_count


## input: dictionary of (emotion, value)
## output: dictionary of (emotion, 1) for emotions passed the threshold
def accumulate_threshold(count, percentage):
	## temp_dict -> { 0.3: ['happy', 'angry'], 0.8: ['sleepy'], ... }
	## (count)	    { 2:   ['bouncy', 'sleepy', 'hungry', 'creative'], 3: ['cheerful']}
	temp_dict = defaultdict( list ) 
	for e in count:
		temp_dict[count[e]].append(e)
	
	## temp_list -> [ (0.8, ['sleepy']), (0.3, ['happy', 'angry']), ... ] ((sorted))
	## (count)	    [ (3, ['cheerful']), (2,   ['bouncy', 'sleepy', 'hungry', 'creative'])]
	temp_list = temp_dict.items()
	temp_list.sort(reverse=True)

	th = percentage * sum( count.values() )
	current_sum = 0
	selected_emotions = []

	while current_sum < th:
		top = temp_list.pop(0)
		selected_emotions.extend( top[1] )
		current_sum += top[0] * len(top[1])

	return dict( zip(selected_emotions, [1]*len(selected_emotions)) )


## input: count <dict> emotion --> count
## output: patscore <dict> emotion --> score


## output: a dictionary of (emotion, patfeature) according to different featureValueType 
def get_patfeature(pattern, udocID):
	########################################################################################
	## [Options]
	## 		config.minCount
	## 		config.featureValueType
	## 		config.cut
	########################################################################################

	# count <dict> emotion --> patcount
	# {
	#	'aggravated': 3,
	#  	'amused': 2,
	#  	'anxious': 3, ...
	# }
	logging.info('get count of "%s"' % (color.render(pattern,'g') ))
	count = get_patcount(pattern) # pattern count

	if not count: return {}

	## remove self count using --remove argument
	logging.info('remove self count of "%s" in udocID: %s' % (color.render(pattern,'g'), color.render(str(udocID),'lc')) )
	count = remove_self_count(udocID, pattern, count, category=config.category)

	# check if total patcount < min_count
	if sum( count.values() ) < config.minCount: return {}
	
	percentage = config.cutoffPercentage/float(100)
	binary_vector = accumulate_threshold(count, percentage)

	## binary vector
	# if config.featureValueType == 'b':
	# 	return binary_vector
	
	# ## pattern count (frequency)
	# elif config.featureValueType == 'f':	
	# 	return { e: count[e] for e in binary_vector if binary_vector[e] == 1 }

	## pattern score
	# elif config.featureValueType == 's':
	# pattern_score = pattern_scoring(count)
	pattern_score = util.pattern_scoring_function(count)
	return { e: pattern_score[e] for e in binary_vector if binary_vector[e] == 1 }

	# else:
		# return False

def get_document_feature(udocID):

	docfeature = Counter()

	## find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	logging.info('\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats)))

	for pat in pats:

		patfeature = get_patfeature(pat['pattern'], udocID)

		for e in patfeature: 
			docfeature[e] += patfeature[e]

	return docfeature

## category: emotion or polarity
def create_document_features(category):

	## list of category
	
	categories = [ x[category] for x in co_cate.find( { 'label': category } ) ]
	logging.debug('found %d categories' % len(categories))

	for (ie, gold_category) in enumerate(categories):

		## get all document with emotions <gold_emotion> (ldocID: 0-799 for training, 800-999 for testing)
		docs = list( co_docs.find( { category: gold_category } ) )

		logging.debug('%d > %s ( %d docs )' % ( ie, color.render(gold_category, 'g'), len(docs) ))

		for doc in docs:
			get_document_feature(udocID=doc['udocID'])
			exit(0)
			mdoc = {
				category: gold_category,
				"udocID": doc['udocID'],
				"feature": get_document_feature(udocID=doc['udocID']).items(),
				"setting": setting_id # looks like "5369fb11d4388c0aa4c5ca4e"
			}
			co_feature.insert(mdoc)

	co_feature.create_index("setting")

if __name__ == '__main__':

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
				'                 k: cut at k%']),
		# ('-r', ['-r: remove self count',
		# 		"                 0: dont't remove anything",
		# 		'                 1: minus-one',
		# 		'                 f: minus-frequency']),
		('--debug', ['--debug: run in debug mode'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hf:n:c:vr:',['help', 'featureValueType=', 'minCount=', 'cut', 'verbose', 'debug'])
	except getopt.GetoptError:
		config.help(config.patternEmotionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.patternEmotionFeat_name, addon=add_opts)
		elif opt in ('-f'): config.featureValueType = arg.strip()
		elif opt in ('-n'): config.minCount = int( arg.strip() )
		elif opt in ('-c'): config.cutoffPercentage = int( arg.strip() )
		elif opt in ('-v','--verbose'): config.verbose = True
		# elif opt in ('-r'): remove_type = arg.strip()
		elif opt in ('--debug'): config.debug = True

	loglevel = logging.DEBUG if config.verbose else logging.INFO
	logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)

	## select mongo collections
	co_cate = db[config.co_category_name] ## db.polarity or db.emotions
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_lexicon = db[config.co_lexicon_name]
	co_ptc = db[config.co_lexicon_pattern_tc_name]

	index_check_list = [(co_docs, config.category), (co_pats, 'udocID'), (co_lexicon, 'pattern')]
	util.check_indexes(check_list=index_check_list, verbose=config.verbose)

	# exit(0)
	

	# target mongo collections
	if config.debug: # insert to a debug collection
		co_setting = db['debug.features.settings']
		co_feature = db['debug.features.pattern_emotion']
	else:
		co_setting = db['features.settings']
		co_feature = db['features.pattern_emotion']		


	## insert metadata
	setting = { 
		"feature_name": "pattern_emotion", 
		"feature_value_type": config.featureValueType,
		"min_count": config.minCount,
		"cutoff_percentage": config.cutoffPercentage,
		# "remove": remove_type
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	# setting_id = str(co_setting.insert( setting ))

	## run
	print 'load_mongo_docs'
	mongo_docs = util.load_mongo_docs(co_docs)

	# if remove_type == 'f':
	print 'load_lexicon_pattern_total_count'
	PatTC = util.load_lexicon_pattern_total_count(co_ptc)

	print 'create_document_features'
	create_document_features(category=config.category)
