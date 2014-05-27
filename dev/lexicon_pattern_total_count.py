import pymongo
from collections import defaultdict, Counter

db = pymongo.Connection('localhost')['LJ40K']

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
