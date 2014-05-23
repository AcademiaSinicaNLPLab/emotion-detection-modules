import config
import sys, pymongo, color
from collections import defaultdict, Counter
from nltk.stem.wordnet import WordNetLemmatizer

db = pymongo.Connection(config.mongo_addr)[config.db_name]

keyword_list = []
lmtzr = WordNetLemmatizer()

## input: word
## output: a dictionary of (emotion: count)
def get_keyword_count(word):
	mdoc = co_keyword_lexicon.find_one({ 'keyword': word })
	if mdoc: return mdoc['count']
	else: return {}


## input: dictionary of (emotion, count)
## output: dictionary of (emotion, count)
def remove_self_count(count_dict, udocID):
	 
	mdoc = co_docs.find_one( {'udocID': udocID} )
	
	## ldocID: 0-799	
	if mdoc['ldocID'] < 800: 

			count_dict[mdoc['emotion']] = count_dict[mdoc['emotion']] - 1
			if count_dict[mdoc['emotion']] == 0 :
				del count_dict[mdoc['emotion']]
	
	return count_dict


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


## input: udocID
## output: a dictionary of (word: occurrence)
def get_keyword_feature(udocID):

	keywordFeature = Counter()

	## find all words in the document <udocID>
	words = []
	POSs = []
	sent_mdocs = list( co_sents.find( {'udocID': udocID} ) )
	for sent_mdoc in sent_mdocs:
		words.extend( sent_mdoc['sent'].split(' ') ) # words: list of 'happy'
		POSs.extend( sent_mdoc['sent_pos'].split(' ') ) # POSs: list of 'happy/JJ'

	if config.verbose:
		print >> sys.stderr, '\t%s (%d words)\t' % (  color.render('#' + str(udocID), 'y'), len(words))

	for idx, word in enumerate(words):
		word = word.lower()

		if config.lemma: 
			POS = POSs[idx].split('/').pop()
			if POS.startswith('J'): pos = 'a'
			elif POS.startswith('V'): pos = 'v'
			elif POS.startswith('R'): pos = 'r'
			else: pos = 'n'
			word = lmtzr.lemmatize(word, pos)

		count = get_keyword_count(word)
		if count: 
			count = remove_self_count( count,  udocID )
			for e in accumulate_threshold(count):
				keywordFeature[ e ] += 1

	return keywordFeature

def create_keyword_features():

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
				"feature": get_keyword_feature(udocID=doc['udocID']).items(),
				"setting": setting_id # looks like "5369fb11d4388c0aa4c5ca4e"
			}
			co_feature.insert(mdoc)

	co_feature.create_index("setting")


if __name__ == '__main__':

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_sents = db[config.co_sents_name]

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.keyword_emotion']

	## input arguments
	import getopt

	add_opts = [
		('-k', ['-k: keyword set in WordNetAffect',
				'                 0: basic',
				'                 1: extend']),
		('--lemma', ['--lemma: use word lemma when looking for keywords'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hk:v',['help', 'keyword_type=', 'lemma', 'verbose'])
	except getopt.GetoptError:
		config.help(config.keywordEmotionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.keywordEmotionFeat_name, addon=add_opts)
		elif opt in ('-k','--keyword_type'): 
			if int(arg.strip()) == 0: config.keyword_type = 'basic'
			elif int(arg.strip()) == 1: config.keyword_type = 'extend'
		elif opt in ('--lemma'): config.lemma = True
		elif opt in ('-v','--verbose'): config.verbose = True

	## create metadata
	setting = { 
		"feature_name": "keyword_emotion", 
		"keyword_type": config.keyword_type,
		"lemma": config.lemma 
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

	## run
	import time
	s = time.time()	
	create_keyword_features()
	print 'Time total:',time.time() - s,'sec'

