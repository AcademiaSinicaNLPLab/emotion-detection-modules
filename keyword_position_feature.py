import config
import sys, pymongo, color
from collections import defaultdict, Counter
from nltk.stem.wordnet import WordNetLemmatizer

db = pymongo.Connection(config.mongo_addr)[config.db_name]

keyword_list = []
lmtzr = WordNetLemmatizer()

## input: udocID
## output: a dictionary of (word: occurrence)
def get_keyword_feature(udocID):

	sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
	total_words = sum([sents[x] for x in sents])

	th1 = total_words * config.begPercentage/float(100)
	th2 = total_words * (config.begPercentage+config.midPercentage)/float(100)

	keywordFeature = Counter()

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
			if POS.startswith('J'): pos = 'a'
			elif POS.startswith('V'): pos = 'v'
			elif POS.startswith('R'): pos = 'r'
			else: pos = 'n'
			word = lmtzr.lemmatize(word, pos)

		if wordIDs[idx] <= th1: position = 'beginning'
		elif wordIDs[idx] <= th2: position = 'middle'
		else: position = 'end'

		if word in keyword_list:
			key = '@'+ position + '_' + word
			keywordFeature[ key ] += 1

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
	co_sents = db[config.co_sents_name]
	co_keywords = db['resource.WordNetAffect']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.keyword_position']

	## input arguments
	import getopt

	add_opts = [
		('-b', ['-b: percentage of beginning section']),
		('-m', ['-m: percentage of middle section']),
		('-e', ['-e: percentage of ending section']),
		('-k', ['-k: keyword set in WordNetAffect',
				'                 0: basic',
				'                 1: extend']),
		('--lemma', ['--lemma: use word lemma when looking for keywords'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hb:m:e:k:v',['help', 'begPercentage=', 'midPercentage=', 'endPercentage=', 'keyword_type=', 'lemma', 'verbose'])
	except getopt.GetoptError:
		config.help(config.keywordPositionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.keywordPositionFeat_name, addon=add_opts)
		elif opt in ('-b'): config.begPercentage = int(arg.strip())
		elif opt in ('-m'): config.midPercentage = int(arg.strip())
		elif opt in ('-e'): config.endPercentage = int(arg.strip())
		elif opt in ('-k','--keyword_type'): 
			if int(arg.strip()) == 0: config.keyword_type = 'basic'
			elif int(arg.strip()) == 1: config.keyword_type = 'extend'
		elif opt in ('--lemma'): config.lemma = True
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "keyword_position",
		"section": "b"+ str(config.begPercentage) + "_m" + str(config.midPercentage) + "_e" + str(config.endPercentage),  
		"keyword_type": config.keyword_type,
		"lemma": config.lemma 
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## create keyword_list
	keyword_list = [ mdoc['word'] for mdoc in list( co_keywords.find( {'type': config.keyword_type} ) ) ]

	## run
	import time
	s = time.time()	
	create_keyword_features()
	print 'Time total:',time.time() - s,'sec'

