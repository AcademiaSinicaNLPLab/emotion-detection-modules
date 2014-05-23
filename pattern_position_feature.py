import config
import sys, pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

cache = {}

## input: pattern
## output: number of total occurrence
def get_total_count(pattern):

	global cache

	if pattern not in cache:
		
		query = { 'pattern': pattern.lower() }
		projector = { '_id': 0, 'count':1 }
		res = co_nestedLexicon.find_one(query, projector)
		
		if not res:
			cache[pattern] = 0
		else:
			cache[pattern] = sum( [ res['count'][e] for e in res['count'] ] )

	return cache[pattern]

## input: udocID
## output: a dictionary of (pattern: occurrence)
def get_pattern_feature(udocID):

	sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
	usentID_offset = min(sents)
	total_words = sum([sents[x] for x in sents])

	th1 = total_words * config.begPercentage/float(100)
	th2 = total_words * (config.begPercentage+config.midPercentage)/float(100)

	patFeature = Counter()

	## find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	for pat in pats:

		if get_total_count(pat['pattern']) >= config.min_count:

			## find pattern position ( beginning/middle/end )
			lanchorID = sum([sents[usentID_offset+i] for i in range(pat['usentID'] - usentID_offset)]) + pat['anchor_idx']
			if lanchorID <= th1: position = 'beginning'
			elif lanchorID <= th2: position = 'middle'
			else: position = 'end'

			key = '@'+ position + '_' + pat['pattern']
			patFeature[ key ] += 1

	return patFeature

def create_pattern_features():

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
				"feature": get_pattern_feature(udocID=doc['udocID']).items(),
				"setting": setting_id # looks like "5369fb11d4388c0aa4c5ca4e"
			}
			co_feature.insert(mdoc)

	co_feature.create_index("setting")


if __name__ == '__main__':

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_nestedLexicon = db['lexicon.nested']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.pattern_position']

	## input arguments
	import getopt

	add_opts = [
		('-b', ['-b: percentage of beginning section']),
		('-m', ['-m: percentage of middle section']),
		('-e', ['-e: percentage of ending section']),
		('-l', ['-l: minimum occurrence of a pattern',
				'                 n: at least occurs < n > times for each pattern'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hb:m:e:l:v',['help', 'begPercentage=', 'midPercentage=', 'endPercentage=', 'min_count=', 'verbose'])
	except getopt.GetoptError:
		config.help(config.patternPositionFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.patternPositionFeat_name, addon=add_opts)
		elif opt in ('-b'): config.begPercentage = int(arg.strip())
		elif opt in ('-m'): config.midPercentage = int(arg.strip())
		elif opt in ('-e'): config.endPercentage = int(arg.strip())
		elif opt in ('-l','--limit'): config.min_count = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "pattern_position", 
		"section": "b"+ str(config.begPercentage) + "_m" + str(config.midPercentage) + "_e" + str(config.endPercentage), 
		"min_count": config.min_count 
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## run
	import time
	s = time.time()	
	create_pattern_features()
	print 'Time total:',time.time() - s,'sec'

