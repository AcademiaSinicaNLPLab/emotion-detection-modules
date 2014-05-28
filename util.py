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
#  340 
def load_lexicon_pattern_total_count(co_ptc):
	PatTC = {}
	# co_ptc = db['lexicon.pattern_total_count']
	if not os.path.exists('PTC.lexicon.pkl'):
		if not os.path.exists('cache'): os.mkdir('cache')
		for mdoc in co_ptc.find():
			PatTC[mdoc['udocID']] = {pat: count for pat, count in mdoc['pats']}
		pickle.dump(PatTC, open('PTC.lexicon.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		PatTC = pickle.load(open('PTC.lexicon.pkl','rb'))
	return PatTC