import pickle, os

## load entire mongo.LJ40K.docs into memory
def load_mongo_docs(co_docs):
	mongo_docs = {}
	if not os.path.exists('cache/mongo_docs.pkl'):
		if not os.path.exists('cache'): os.mkdir('cache')
		for mdoc in co_docs.find({}, {'_id':0}):
			udocID = mdoc['udocID']
			del mdoc['udocID']
			mongo_docs[udocID] = mdoc
		pickle.dump(mongo_docs, open('cache/mongo_docs.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		mongo_docs = pickle.load(open('cache/mongo_docs.pkl','rb'))
	return mongo_docs

##  PTC[33680]['i love you']
##  340 
def load_lexicon_pattern_total_count(co_ptc, lexicon_type='lexicon'):
	PatTC = {}
	# co_ptc = db['lexicon.pattern_total_count']
	pkl_path = 'cache/PTC.'+lexicon_type+'.pkl'
	if not os.path.exists():
		for mdoc in co_ptc.find():
			PatTC[mdoc['udocID']] = {pat: count for pat, count in mdoc['pats']}
		if not os.path.exists('cache'): os.mkdir('cache')
		pickle.dump(PatTC, open(pkl_path,'wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		PatTC = pickle.load(open(pkl_path,'rb'))
	return PatTC


## KwTC[0]['bad']
## 1
def load_lexicon_keyword_total_count(co_ktc):
	KwTC = {}
	# co_ktc = db['lexicon.keyword_total_count']
	if not os.path.exists('cache/KwTC.lexicon.pkl'):
		for mdoc in co_ktc.find():
			KwTC[mdoc['udocID']] = {kw: count for kw, count in mdoc['keywords']}
		if not os.path.exists('cache'): os.mkdir('cache')
		pickle.dump(KwTC, open('cache/KwTC.lexicon.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		KwTC = pickle.load(open('cache/KwTC.lexicon.pkl','rb'))
	return KwTC