import config
import sys, pymongo, color
from collections import defaultdict, Counter
from nltk.stem.wordnet import WordNetLemmatizer

from util import load_mongo_docs, load_lexicon_keyword_total_count

db = pymongo.Connection(config.mongo_addr)[config.db_name]

lmtzr = WordNetLemmatizer()

# global cache for keyword
cache = {}

# global cache for mongo.LJ40K.docs
mongo_docs = {}

# global cache for mongo.LJ40K.lexicon.keyword_total_count
KwTC = {}

## remove_type = '0', '1', 'f'
remove_type = '0'


## input: word
## output: a dictionary of (emotion: count)
def get_keyword_count(word):

	global cache

	if word not in cache:
		mdoc = co_keyword_lexicon.find_one({ 'keyword': word })
		if mdoc: 
			cache[word] = mdoc['count']
		else: 
			cache[word] = {}

	return cache[word]


## input: dictionary of (emotion, count)
## output: dictionary of (emotion, count)
def remove_self_count(udocID, keyword, count_dict):

	global mongo_docs
	mdoc = mongo_docs[udocID] # use pre-loaded

	new_count = dict(count_dict)

	if new_count: 

		## ldocID: 0-799	
		if mdoc['ldocID'] < 800: 

			if remove_type == '0':
				pass
			elif remove_type == '1':
				new_count[mdoc['emotion']] = new_count[mdoc['emotion']] - 1
			elif remove_type == 'f':
				new_count[mdoc['emotion']] = new_count[mdoc['emotion']] - KwTC[udocID][keyword]

			# new_count[mdoc['emotion']] = new_count[mdoc['emotion']]
			if new_count[mdoc['emotion']] == 0 :
				del new_count[mdoc['emotion']]

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
def scoring(count):

	score = {}

	for emo in count:

		SUM = float( sum( [ count[key] for key in count if key != emo ] ) )
		SUMSQ = float( sum( [ (count[key] ** 2) for key in count if key != emo ] ) )
		
		emo_value = float( count[emo] )
		not_emo_value = float( SUMSQ/( SUM + 0.9 ** SUM ) )
		
		score[emo] = emo_value / (emo_value + not_emo_value)

	return score


## input: udocID
## output: a dictionary of (word: occurrence)
def get_keyword_feature(udocID):

	keywordFeature = Counter()

	sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
	total_words = sum([sents[x] for x in sents])

	th1 = total_words * config.begPercentage/float(100)
	th2 = total_words * (config.begPercentage+config.midPercentage)/float(100)

	## find all words in the document <udocID>
	words = []
	POSs = []
	wordIDs = []
	sent_mdocs = list( co_sents.find( {'udocID': udocID} ) )
	for sent_mdoc in sent_mdocs:
		
		## words: list of 'happy'
		words.extend( sent_mdoc['sent'].split(' ') ) 

		## POSs: list of 'happy/JJ'
		POSs.extend( sent_mdoc['sent_pos'].split(' ') ) 
		
		## wordIDs: list of 'word id' 
		wordID_offset = 0
		for key in sents:
			if key < sent_mdoc['usentID']: wordID_offset += sents[key]
		wordIDs.extend( [ (x+1+wordID_offset) for x in range(sents[ sent_mdoc['usentID'] ]) ] )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d words)\t' % (  color.render('#' + str(udocID), 'y'), len(words))

	for idx, word in enumerate(words):
		word = word.lower()

		if config.lemma: 
			POS = POSs[idx].split('/').pop()
			if POS.startswith('N'): pos = 'n'
			elif POS.startswith('V'): pos = 'v'
			elif POS.startswith('J'): pos = 'a'
			elif POS.startswith('R'): pos = 'r'
			else: pos = None
			if pos: # only lemmatize certain pos types
				word = lmtzr.lemmatize(word, pos)


		if wordIDs[idx] <= th1: position = 'beginning'
		elif wordIDs[idx] <= th2: position = 'middle'
		else: position = 'end'



		count = get_keyword_count(word)
		if not count: return {}
		count = remove_self_count( udocID, word, count )

		percentage = config.cutoffPercentage/float(100)
		binary_vector = accumulate_threshold(count, percentage)
			
		if config.featureValueType == 'b':
			for emo in binary_vector:
				key = '@'+ position + '_' + emo
				keywordFeature[key] += binary_vector[emo] 
		
		## pattern count (frequency)
		elif config.featureValueType == 'f':	
			count_vector =  { e: count[e] for e in binary_vector if binary_vector[e] == 1 }
			for emo in count_vector:
				key = '@'+ position + '_' + emo
				keywordFeature[key] += count_vector[emo] 

		## keyword score
		elif config.featureValueType == 's':
			keyword_score = scoring(count)
			score_vector = { e: keyword_score[e] for e in binary_vector if binary_vector[e] == 1 }
			for emo in score_vector:
				key = '@'+ position + '_' + emo
				keywordFeature[key] += score_vector[emo] 

		else:
			return False

	return keywordFeature


def create_keyword_features():

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
				"feature": get_keyword_feature(udocID=doc['udocID']).items(),
				"setting": setting_id # looks like "5369fb11d4388c0aa4c5ca4e"
			}
			co_feature.insert(mdoc)

	co_feature.create_index("setting")


if __name__ == '__main__':

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_sents = db[config.co_sents_name]
	co_keywords = db['resource.WordNetAffect']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.keyword_emotion_position']

	co_ktc = db['lexicon.keyword_total_count']

	## input arguments
	import getopt

	add_opts = [
		('-b', ['-b: percentage of beginning section']),
		('-m', ['-m: percentage of middle section']),
		('-e', ['-e: percentage of ending section']),
		('-k', ['-k: keyword set in WordNetAffect',
				'                 0: basic',
				'                 1: extend']),
		('--lemma', ['--lemma: use word lemma when looking for keywords']),
		('-f', ['-f: feature value type',
				'                 b: binary vector',
				'                 f: keyword count (frequency)',
				'                 s: keyword score']),
		('-c', ['-c: cut off by accumulated count percentage',
				'                 k: cut at k%']),
		('-r', ['-r: remove self count',
				"                 0: dont't remove anything",
				'                 1: minus-one',
				'                 f: minus-frequency']),
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hb:m:e:k:f:c:r:v',['help', 'begPercentage=', 'midPercentage=', 'endPercentage=', 'keyword_type=', 'lemma', 'verbose'])
	except getopt.GetoptError:
		config.help(config.keywordEmotionPositionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.keywordEmotionPositionFeat_name, addon=add_opts)
		elif opt in ('-b'): config.begPercentage = int(arg.strip())
		elif opt in ('-m'): config.midPercentage = int(arg.strip())
		elif opt in ('-e'): config.endPercentage = int(arg.strip())
		elif opt in ('-k','--keyword_type'): 
			if int(arg.strip()) == 0: config.keyword_type = 'basic'
			elif int(arg.strip()) == 1: config.keyword_type = 'extend'
		elif opt in ('--lemma'): config.lemma = True
		elif opt in ('-f'): config.featureValueType = arg.strip()		
		elif opt in ('-c'): config.cutoffPercentage = int( arg.strip() )
		elif opt in ('-r'): remove_type = arg.strip()
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "keyword_emotion_position",
		"section": "b"+ str(config.begPercentage) + "_m" + str(config.midPercentage) + "_e" + str(config.endPercentage),  
		"keyword_type": config.keyword_type,
		"lemma": config.lemma,
		"feature_value_type": config.featureValueType,
		"cutoff_percentage": config.cutoffPercentage,
		"remove": remove_type
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## specify keyword lexicon
	if config.keyword_type == 'basic':
		if config.lemma: 
			co_keyword_lexicon = db['lexicon.keyword.basic.w_lemma']
		else: 
			co_keyword_lexicon = db['lexicon.keyword.basic.wo_lemma']
	elif config.keyword_type == 'extend':
		if config.lemma: 
			co_keyword_lexicon = db['lexicon.keyword.extend.w_lemma']
		else: 
			co_keyword_lexicon = db['lexicon.keyword.extend.wo_lemma']

	## create keyword_list
	# keyword_list = [ mdoc['word'] for mdoc in list( co_keywords.find( {'type': config.keyword_type} ) ) ]


	## run
	print 'load_mongo_docs'
	mongo_docs = load_mongo_docs(co_docs)

	if remove_type == 'f':
		print 'load_lexicon_keyword_total_count'
		KwTC = load_lexicon_keyword_total_count(co_ktc)

	print 'create_keyword_features'
	create_keyword_features()

