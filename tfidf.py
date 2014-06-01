import sys, os
sys.path.append('../')
import pickle, math
import mathutil
import config
import pymongo, color
from collections import defaultdict, Counter
from nltk.stem.wordnet import WordNetLemmatizer

db = pymongo.Connection(config.mongo_addr)[config.db_name]

keyword_list = []
lmtzr = WordNetLemmatizer()
D = 32000

## udocID --> ldocID
def build_u2l():
	u2l = {}
	if not os.path.exists('cache/u2l.pkl'):
		u2l = {mdoc['udocID']: mdoc['ldocID'] for mdoc in db['docs'].find()}
		pickle.dump(u2l, open('cache/u2l.pkl', 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		u2l = pickle.load(open('cache/u2l.pkl', 'rb'))
	return u2l

## word (lower) --> udocID --> wordcount
def build_TWC(u2l, lemmatize=False):
	fn = 'TWC.pkl' if not lemmatize else 'TWC.lemma.pkl'
	if not os.path.exists('cache/u2l.pkl'):
		TWC = defaultdict(Counter)
		for udocID in range(40000):
			if u2l[udocID] >= 800: continue ## not in training data
			for mdoc in db['sents'].find({'udocID':udocID}):
				for word_pos in mdoc['sent_pos'].split(' '):
					word_pos = word_pos.split('/')
					word, POS = '/'.join(word_pos[:-1]).lower(), word_pos[-1]
					if lemmatize:
						if POS.startswith('N'): pos = 'n'
						elif POS.startswith('J'): pos = 'a'
						elif POS.startswith('V'): pos = 'v'
						elif POS.startswith('R'): pos = 'r'
						else: pos = None
						if pos:
							word = lmtzr.lemmatize(word, pos)
					TWC[word][udocID] += 1

		pickle.dump(TWC, open('cache/'+fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		TWC = pickle.load(open('cache/'+fn, 'rb'))
	return TWC

def build_nt(TWC, lemmatize=True):
	fn = 'cache/N.pkl' if not lemmatize else 'cache/N.lemma.pkl'
	if not os.path.exists(fn):
		N = {}
		for t in TWC:
			N[t] = mathutil.entropy(TWC[t].values())
		pickle.dump(N, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		N = pickle.load(open(fn, 'rb'))
	return N

def build_K(u2l, lemmatize=True): # cardinality of |d|, i.e., K|d|
	fn = 'cache/K.pkl' if not lemmatize else 'cache/K.lemma.pkl'
	if not os.path.exists(fn):
		K = {} # udocID --> K|d|
		for udocID in range(40000):
			if u2l[udocID] >= 800: continue ## not in training data
			kd = sum([mdoc['sent_length'] for mdoc in db['sents'].find({'udocID':udocID})])
			K[udocID] = kd
		pickle.dump(K, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		K = pickle.load(open(fn, 'rb'))
	return K
		

def TF1_IDF1(TWC, D, lemmatize=False):
	fn = 'cache/TF1IDF1.pkl' if not lemmatize else 'cache/TF1IDF1.lemma.pkl'
	if not os.path.exists(fn):
		TF1IDF1 = defaultdict(Counter)
		for t in TWC:
			Ft = len(TWC[t])
			idf1 = D/float(Ft)
			for udocID in TWC[t]:
				wc = TWC[t][udocID]
				tf1 = 1+math.log(wc,2)
				TF1IDF1[t][udocID] = tf1 * idf1
		pickle.dump(TF1IDF1, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		TF1IDF1 = pickle.load(open(fn, 'rb'))
	return TF1IDF1

def TF1_IDF2(TWC, D, N, lemmatize=False):
	fn = 'cache/TF1IDF2.pkl' if not lemmatize else 'cache/TF1IDF2.lemma.pkl'
	if not os.path.exists(fn):
		max_nt = max(N.values())
		TF1IDF2 = defaultdict(Counter)
		for t in TWC:
			idf2 = max_nt - N[t]
			for udocID in TWC[t]:
				wc = TWC[t][udocID]
				tf1 = 1+math.log(wc,2)
				TF1IDF2[t][udocID] = tf1 * idf2
		pickle.dump(TF1IDF2, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		TF1IDF2 = pickle.load(open(fn, 'rb'))
	return TF1IDF2

def TF3_IDF2(TWC, D, N, K, lemmatize=False):
	fn = 'cache/TF3IDF2.pkl' if not lemmatize else 'cache/TF3IDF2.lemma.pkl'
	if not os.path.exists(fn):	
		TF3IDF2 = defaultdict(Counter)
		delta_d = float(sum(K.values())/float(len(K)))
		max_nt = max(N.values())

		for t in TWC:
			idf2 = max_nt - N[t]
			for udocID in TWC[t]:
				wc = TWC[t][udocID]
				tf3 = wc/float( wc + K[udocID]/delta_d )
				TF3IDF2[t][udocID] = tf3 * idf2
		pickle.dump(TF3IDF2, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		TF3IDF2 = pickle.load(open(fn, 'rb'))
	return TF3IDF2

## change  word --> udocID --> wc
##     to  udocID --> word --> wc
def inverse_key(TFIDF):
	inversed = defaultdict(dict)
	for t in TFIDF:
		for udocID in TFIDF[t]:
			tfidf = TFIDF[t][udocID]
			inversed[udocID][t] = tfidf
	return inversed

