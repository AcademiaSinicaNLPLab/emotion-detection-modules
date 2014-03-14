import pickle	
import pymongo	
from collections import Counter

emoList = pickle.load(open('emoList.pkl', 'r'))

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']	
co_docs = db['docs']	
co_pats = db['pats']		
co_lexicon = db['lexicon']
patCount = dict()	

# count patterns
for _emo in emoList:
	patCount[_emo] = Counter()
	for _ldocID in range(800):
		_udocID = co_docs.find_one( { 'emotion': _emo, 'ldocID': _ldocID} )['udocID']
		mdocs = list( co_pats.find( {'udocID': _udocID} ) )
		for mdoc in mdocs:
			patCount[_emo][mdoc['pattern'].lower()] += 1

# build lexicon
for _emo in emoList:
	for _pat in patCount[_emo].keys():
		co_lexicon.insert( { 'pattern': _pat, 'emotion': _emo, 'count': patCount[_emo][_pat] } )

