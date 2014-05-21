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
	## type 3: type 2 + ignore patterns with total occurrence < 4 (1, 2, 3)  
	## type 4: type 2 + remove the pattern occurrence counted from oneself (for ldocID 0-799)   
	## type 5: type 3 + remove the pattern occurrence counted from oneself (for ldocID 0-799)
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
	co_feature = db['features.position']

	## input arguments
	import getopt
	
	add_opts = [
		('-b', ['-b: percentage of beginning section']),
		('-m', ['-m: percentage of middle section']),
		('-e', ['-e: percentage of ending section']),
		('-c', ['-c: counting unit for document segmentation',
				'                 0: number of words',
				'                 1: number of sentences (not implemented yet)']),
		('-f', ['-f: feature value computation',
				'                 0: pattern scores (patscore_p2_s0)', 
				'                 1: accumulated threshold by 0.68 (1 std) using pattern scores',
				'                 2: accumulated threshold by 0.68 (1 std) using pattern count',
				'                 3: type 2 + ignore those with total occurrence < 4 (1, 2, 3)', 
				'                 4: type 2 + remove the pattern occurrence counted from oneself (for ldocID 0-799)',   
				'                 5: type 3 + remove the pattern occurrence counted from oneself (for ldocID 0-799)'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hb:m:e:c:f:v',['help','begPercentage=', 'midPercentage=', 'endPercentage=', 'countingUnitType=', 'featureValueType=', 'verbose'])
	except getopt.GetoptError:
		config.help(config.positionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.positionFeat_name, addon=add_opts)
		elif opt in ('-b'): config.begPercentage = int(arg.strip())
		elif opt in ('-m'): config.midPercentage = int(arg.strip())
		elif opt in ('-e'): config.endPercentage = int(arg.strip())
		elif opt in ('-c'): config.countingUnitType = int(arg.strip())
		elif opt in ('-f'): config.featureValueType = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "position", 
		"section": "b"+ str(config.begPercentage) + "_m" + str(config.midPercentage) + "_e" + str(config.endPercentage), 
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

	print record
