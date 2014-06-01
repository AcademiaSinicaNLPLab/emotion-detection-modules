import pymongo
from collections import defaultdict, Counter

db = pymongo.Connection('doraemon.iis.sinica.edu.tw')['LJ40K']

def create_lexicon_pattern_total_count():
	PatTC = defaultdict(Counter)

	for mdoc in db['pats'].find():
		pat = mdoc['pattern'].lower()
		udocID = mdoc['udocID']
		PatTC[udocID][pat] += 1

	co = db['lexicon.pattern_total_count']
	for udocID in PatTC:
		mdoc = { 'udocID': udocID, 'pats': PatTC[udocID].items() }
		co.insert(mdoc)
	co.create_index('udocID')

def create_lexicon_pattern_position_total_count():
	
	PatTC = defaultdict(Counter)

	udocIDs = [ x['udocID'] for x in list( db['docs'].find() ) ]

	for udocID in udocIDs:

		sents = { x['usentID']:x['sent_length'] for x in list( db['sents'].find( {'udocID': udocID} ) ) }
		usentID_offset = min(sents)
		total_words = sum([sents[x] for x in sents])

		th1 = total_words * 0.2
		th2 = total_words * 0.8

		pats = list( db['pats'].find( {'udocID': udocID} ) )
		
		for pat in pats:
			
			lanchorID = sum([sents[usentID_offset+i] for i in range(pat['usentID'] - usentID_offset)]) + pat['anchor_idx']
			if lanchorID <= th1: position = 'beginning'
			elif lanchorID <= th2: position = 'middle'
			else: position = 'end'

			key = '#' +  pat['pattern'].lower() + '@' + position
			PatTC[udocID][key] += 1

	co = db['lexicon.pattern_position_total_count']
	for udocID in PatTC:
		mdoc = { 'udocID': udocID, 'pats': PatTC[udocID].items() }
		co.insert(mdoc)
	co.create_index('udocID')


def create_lexicon_keyword_total_count(wordType='extend', lemma=True):

	from nltk.stem.wordnet import WordNetLemmatizer
	KwTC = defaultdict(Counter)

	co_docs = db['docs']
	co_sents = db['sents']
	co_keywords = db['resource.WordNetAffect']

	lmtzr = WordNetLemmatizer()
	emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}, {'_id':0, 'emotion':1})])
	keyword_list = set( [ x['word'].lower() for x in list( co_keywords.find({ 'type': wordType }) ) ] )

	for sent_mdoc in co_sents.find():
		# extract words, pos tags
		words = map(lambda x:x.lower(), sent_mdoc['sent'].strip().split(' '))
		POSs = [x.split('/')[-1] for x in sent_mdoc['sent_pos'].split(' ')]
		word_pos = zip(words, POSs)
		udocID = sent_mdoc['udocID']
		
		for word, pos in word_pos:

			word = word.lower()

			if lemma:
				if pos.startswith('N'): pos = 'n'
				elif pos.startswith('V'): pos = 'v'
				elif pos.startswith('J'): pos = 'a'
				elif pos.startswith('R'): pos = 'r'
				else: pos = None
				if pos: # only lemmatize certain pos types
					word = lmtzr.lemmatize(word, pos)

			if word in keyword_list:
				KwTC[udocID][word] += 1

	co = db['lexicon.keyword_total_count']
	for udocID in KwTC:
		mdoc = { 'udocID': udocID, 'keywords': KwTC[udocID].items() }
		co.insert( mdoc )
	co.create_index('udocID')

## load Pattern-Total-Count lexicon
## format
##  PTC[33680]
	# {u'elaine i': 4,
	#  u'elaine you': 12,
	#  u'elainei love': 4,
	#  u'i love': 1057,
	#  u'i love love': 326,
	#  u'i love you': 340,
	# ...}
##  PTC[33680]['i love you']
	#  340 
def load_lexicon_pattern_total_count():
	PatTC = {}
	for mdoc in db['lexicon.pattern_total_count'].find():
		PatTC[mdoc['udocID']] = {pat: count for pat, count in mdoc['pats']}
	return PatTC

 
# KwTC[0]
# {u'bad': 1,
#  u'below': 1,
#  u'best': 1,
#  u'by': 1,
#  u'cut': 1,
#  'do': 1,
#  u'entry': 1,
#  ...
# }
def load_lexicon_keyword_total_count():
	KwTC = {}
	for mdoc in db['lexicon.keyword_total_count'].find():
		KwTC[mdoc['udocID']] = {kw: count for kw, count in mdoc['keywords']}
	return KwTC

if __name__ == '__main__':

	create_lexicon_pattern_position_total_count()


