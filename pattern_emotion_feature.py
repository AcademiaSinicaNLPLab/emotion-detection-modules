import config
import sys, pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

cache = {}
record = []

## input: pat
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


## input: pat
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
def remove_self_count(score_dict, udocID):
	 
	mdoc = co_docs.find_one( {'udocID': udocID} )
	
	## ldocID: 0-799	
	if mdoc['ldocID'] < 800: 

		if mdoc['emotion'] in score_dict:
			score_dict[mdoc['emotion']] = score_dict[mdoc['emotion']] - 1
			if score_dict[mdoc['emotion']] == 0 :
				del score_dict[mdoc['emotion']]
		else:
			record.append(udocID)
	
	return score_dict


## input: pat
## output: a dictionary of (emotion, patfeature) according to different featureValueType 
def get_patfeature(pattern, udocID):
	########################################################################################
	## type 0: pattern scores
	## type 1: accumulated threshold by 0.68 (1 std) using pattern scores    
	## type 2: accumulated threshold by 0.68 (1 std) using pattern occurrence
	## type 3: [type 2] & set min_count=4  
	## type 4: [type 2] & remove the pattern occurrence counted from oneself (for ldocID 0-799)   
	## type 5: [type 3] & remove the pattern occurrence counted from oneself (for ldocID 0-799)
	########################################################################################

	if config.featureValueType == 0:
		return get_patscore(pattern) 

	elif config.featureValueType == 1: 
		score = get_patscore(pattern) # pattern score

	elif config.featureValueType == 2: 
		score = get_patcount(pattern) # pattern occurrence

	elif config.featureValueType == 3: 
		score = get_patcount(pattern) # pattern occurrence
		if sum( [ score[e] for e in score ] ) < 4: return {}

	elif config.featureValueType == 4:
		score = get_patcount(pattern) # pattern occurrence
		score = remove_self_count(score, udocID)

	elif config.featureValueType == 5:
		score = get_patcount(pattern) # pattern occurrence
		score = remove_self_count(score, udocID)
		if sum( [ score[e] for e in score ] ) < 4: return {}		


	## temp_dict -> { 0.3: ['happy', 'angry'], 0.8: ['sleepy'], ... }
	temp_dict = defaultdict( list ) 
	for e in score:
		temp_dict[score[e]].append(e)

	## temp_list -> [ (0.8, ['sleepy']), (0.3, ['happy', 'angry']), ... ] ((sorted))
	temp_list = temp_dict.items()
	temp_list.sort(reverse=True)

	th = 0.68 * sum([score[k] for k in score])
	current_sum = 0
	selected_emotions = []
	while current_sum < th:
		top = temp_list.pop(0)
		selected_emotions.extend( top[1] )
		current_sum += top[0] * len(top[1])

	return dict( zip(selected_emotions, [1]*len(selected_emotions)) )

	# elif ...


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
	co_nestedLexicon = db['lexicon.nested']
	co_patscore = db['patscore_p2_s0']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.pattern_emotion']

	## input arguments
	import getopt
	
	add_opts = [
		('-c', ['-c: counting unit for document segmentation',
				'                 0: number of words',
				'                 1: number of sentences (not implemented yet)']),
		('-f', ['-f: feature value computation',
				'                 0: pattern scores (patscore_p2_s0)', 
				'                 1: accumulated threshold by 0.68 (1 std) using pattern scores',
				'              (X)2: accumulated threshold by 0.68 (1 std) using pattern count',
				'              (X)3: [type 2] & set min_count=4', 
				'                 4: [type 2] & remove the pattern occurrence counted from oneself (for ldocID 0-799)',   
				'                 5: [type 3] & remove the pattern occurrence counted from oneself (for ldocID 0-799)'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hc:f:v',['help', 'countingUnitType=', 'featureValueType=', 'verbose'])
	except getopt.GetoptError:
		config.help(config.patternEmotionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.patternEmotionFeat_name, addon=add_opts)
		elif opt in ('-c'): config.countingUnitType = int(arg.strip())
		elif opt in ('-f'): config.featureValueType = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "pattern_emotion", 
		"counting_unit_type": config.countingUnitType, 
		"feature_value_type": config.featureValueType 
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## run
	import time
	s = time.time()	
	create_document_features(setting_id)
	print 'Time total:',time.time() - s,'sec'

	if record: print record
