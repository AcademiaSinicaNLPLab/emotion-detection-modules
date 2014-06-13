import sys, os
sys.path.append('../')
import pickle, math
import mathutil
import config
import pymongo, color
from collections import defaultdict, Counter
import nltk
from nltk.stem.wordnet import WordNetLemmatizer

db = pymongo.Connection(config.mongo_addr)[config.db_name]

keyword_list = []
lmtzr = WordNetLemmatizer()
D = 32000
fn_postfix = []

overwrite = False

def word_counter(udocID, lemmatize):
	wc = Counter()
	for mdoc in db['sents'].find({'udocID':udocID}):
		for word_pos in mdoc['sent_pos'].split(' '):
			word_pos = word_pos.split('/')
			t, POS = '/'.join(word_pos[:-1]).lower(), word_pos[-1]
			if lemmatize:
				if POS.startswith('N'): pos = 'n'
				elif POS.startswith('J'): pos = 'a'
				elif POS.startswith('V'): pos = 'v'
				elif POS.startswith('R'): pos = 'r'
				else: pos = None
				if pos:
					t = lmtzr.lemmatize(t, pos)
			wc[t] += 1
	return wc

## udocID --> ldocID
def build_u2l():
	u2l = {}
	if not os.path.exists('cache/u2l.pkl'):
		print 'build u2l'
		u2l = {mdoc['udocID']: mdoc['ldocID'] for mdoc in db['docs'].find()}
		pickle.dump(u2l, open('cache/u2l.pkl', 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		print 'load u2l'
		u2l = pickle.load(open('cache/u2l.pkl', 'rb'))
	return u2l

## total word count
## word (lower) --> udocID --> wordcount
def build_TWC(lemmatize, min_count, stoplist, training_udocIDs):

	fn_list = ['TWC']
	fn_list.extend(fn_postfix)
	fn_list.append('pkl')
	fn = os.path.join('cache', '.'.join(fn_list))

	if not os.path.exists(fn) or overwrite:
		print 'build TWC'
		TWC = defaultdict(Counter)
		for udocID in range(40000):
			wc = word_counter(udocID, lemmatize)
			for t in wc:
				## stop word
				if t in stoplist: continue
				TWC[t][udocID] += 1
		## pruning
		pruned = {}
		for t in TWC:
			## min count
			if sum([TWC[t][uid] for uid in TWC[t] if uid in training_udocIDs]) <= min_count: continue
			else:
				pruned[t] = dict(TWC[t])
		pickle.dump(pruned, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		print 'load TWC'
		TWC = pickle.load(open(fn, 'rb'))
	return TWC

def build_nt(TWC, training_udocIDs, lemmatize=True):
	fn = 'cache/N.pkl' if not lemmatize else 'cache/N.lemma.pkl'
	if not os.path.exists(fn):
		print 'build N'
		N = {}
		for t in TWC:
			count_sequence_of_t_in_training_set = [TWC[t][uid] for uid in TWC[t] if uid in training_udocIDs]
			N[t] = mathutil.entropy(count_sequence_of_t_in_training_set)
		pickle.dump(N, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		print 'load N'
		N = pickle.load(open(fn, 'rb'))
	return N

def build_K(lemmatize=True): # cardinality of |d|, i.e., K|d|
	fn = 'cache/K.pkl' if not lemmatize else 'cache/K.lemma.pkl'
	if not os.path.exists(fn):
		print 'build K'
		K = {} # udocID --> K|d|: length of document d
		for udocID in range(40000):
			K[udocID] = sum([mdoc['sent_length'] for mdoc in db['sents'].find({'udocID':udocID})])
		pickle.dump(K, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		print 'load K'
		K = pickle.load(open(fn, 'rb'))
	return K

def create_training(TWC, D, training_udocIDs, tf_type, idf_type, lemmatize=True):
	# fn = 'TF'+tf_type+'x'+'IDF'+idf_type

	fn_list = ['TF'+tf_type+'x'+'IDF'+idf_type]
	fn_list.extend(fn_postfix)
	fn_list.append('train')
	fn_list.append('pkl')
	fn = os.path.join('cache', '.'.join(fn_list))

	K_values_in_training = [K[uid] for uid in K if uid in training_udocIDs]
	delta_d = float(sum(K_values_in_training)/float(len(K_values_in_training))) # average document length, ignore testing docs
	max_nt = max(N.values())

	if not os.path.exists(fn) or overwrite:
		print 'create training'
		training_TFIDF = defaultdict(Counter)
		for udocID in training_udocIDs:
			## training data
			wc = word_counter(udocID, lemmatize)
			for t in wc:

				if t not in TWC: continue

				if tf_type == '1':
					tf = 1+math.log(wc[t],2)  # tf1
				elif tf_type == '3':
					tf = wc[t]/float( wc[t] + K[udocID]/delta_d )
				else:
					tf = False
					print 'invalid tf_type'
					exit(0)

				if idf_type == '1':
					# idf1
					Ft = len([uid for uid in TWC[t] if uid in training_udocIDs]) # only count documents in training
					idf = D/float(Ft) 
				elif idf_type == '2':
					idf = max_nt - N[t]
				else:
					idf = False
					print 'invalid idf_type'
					exit(0)

				tfidf = tf*idf
				training_TFIDF[t][udocID] = tfidf
		
		pickle.dump(training_TFIDF, open( fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		print 'load training'
		training_TFIDF = pickle.load(open(fn, 'rb'))
	return training_TFIDF

def create_testing(TWC, D, testing_udocIDs, tf_type, idf_type, lemmatize=True):

	fn_list = ['TF'+tf_type+'x'+'IDF'+idf_type]
	fn_list.extend(fn_postfix)
	fn_list.append('test')
	fn_list.append('pkl')
	fn = os.path.join('cache', '.'.join(fn_list))

	K_values_in_training = [K[uid] for uid in K if uid not in testing_udocIDs]
	delta_d = float(sum(K_values_in_training)/float(len(K_values_in_training))) # average document length, ignore testing docs
	max_nt = max(N.values())

	if not os.path.exists(fn) or overwrite:
		print 'create testing'
		testing_TFIDF = defaultdict(Counter)
		for udocID in testing_udocIDs:
			## training data
			wc = word_counter(udocID, lemmatize)
			for t in wc:
				if tf_type == '1':
					tf = 1+math.log(wc[t],2) # tf1
				elif tf_type == '3':
					tf = wc[t]/float( wc[t] + K[udocID]/delta_d )
				else:
					tf = False
					print 'invalid tf_type'
					exit(0)

				if idf_type == '1': # idf1
					if t in TWC:
						Ft = len([uid for uid in TWC[t] if uid in training_udocIDs])
						idf = D/float(Ft) 						
					else:
						idf = 1/D # idf1
				elif idf_type == '2': # idf2
					idf = max_nt - N[t]
				else:
					idf = False
					print 'invalid idf_type'
					exit(0)

				tfidf = tf*idf
				testing_TFIDF[t][udocID] = tfidf
		pickle.dump(testing_TFIDF, open( fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		print 'load testing'
		testing_TFIDF = pickle.load(open(fn, 'rb'))
	return testing_TFIDF


def TF1_IDF1(TWC, D, lemmatize=True):
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

def TF1_IDF2(TWC, D, N, lemmatize=True):
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

def TF3_IDF2(TWC, D, N, K, lemmatize=True):
	fn = 'cache/TF3IDF2.pkl' if not lemmatize else 'cache/TF3IDF2.lemma.pkl'
	if not os.path.exists(fn):	
		TF3IDF2 = defaultdict(Counter)
		delta_d = float(sum(K.values())/float(len(K)))
		max_nt = max(N.values())

		IDF2 = {}
		for t in TWC:
			idf2 = max_nt - N[t]
			IDF2[t] = idf2
			for udocID in TWC[t]:
				wc = TWC[t][udocID]
				tf3 = wc/float( wc + K[udocID]/delta_d )
				TF3IDF2[t][udocID] = tf3 * idf2
		pickle.dump(IDF2, open(fn.replace('TF3IDF2','IDF2'), 'wb'), pickle.HIGHEST_PROTOCOL)
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

if __name__ == '__main__':

	# extbasic = 'extend' if len(sys.argv) >= 5 and sys.argv[4] == 'extend' else 'basic'
	# lemmatize = True if len(sys.argv) == 4 and sys.argv[3] == 'lemma' else False
	tf_type = sys.argv[1]
	idf_type = sys.argv[2]
	
	lemmatize = True if '--lemma' in sys.argv else False
	stop = True if '--stop' in sys.argv else False
	overwrite = True if '--overwrite' in sys.argv else False

	min_count = 10
	stoplist = [] if not stop else set(map(lambda x:x.lower(), nltk.corpus.stopwords.words('english')))

	print 'lemmatize:', lemmatize
	print 'stop:', stop
	print 'overwrite:', overwrite
	# print 'extend or basic:', extbasic
	print 'tf:', tf_type
	print 'idf:', idf_type
	print '='*100
	raw_input()

	
	if lemmatize: fn_postfix.append('lemma')
	if stoplist: fn_postfix.append('stop')
	if min_count > 0: fn_postfix.append(str(min_count))
	
	u2l = build_u2l()
	training_udocIDs = set([x for x in u2l if u2l[x] < 800])
	testing_udocIDs  = set([x for x in u2l if u2l[x] >= 800])

	TWC = build_TWC(lemmatize, min_count, stoplist, training_udocIDs)

	K = build_K(lemmatize)

	N = build_nt(TWC, training_udocIDs, lemmatize)

	
	training_TFIDF = create_training(TWC, D, training_udocIDs, tf_type, idf_type, lemmatize=True)

	testing_TFIDF  = create_testing(TWC, D,  testing_udocIDs,  tf_type, idf_type, lemmatize=True)


	# print 'calculating TF1_IDF1'
	# TF1_IDF1(TWC, D, lemmatize)

	# print 'calculating TF1_IDF2'
	# TF1_IDF2(TWC, D, N, lemmatize)

	# print 'calculating TF3_IDF2'
	# TF3_IDF2(TWC, D, N, K, lemmatize)

