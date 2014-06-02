import sys, os
sys.path.append('../')
import pickle, math
import mathutil
import config
import pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

keyword_list = []
D = 32000

overwrite = False

def word_counter(udocID):
	ptc = Counter()
	for mdoc in db['pats'].find({'udocID':udocID}):
		pat = mdoc['pattern']
		ptc[pat] += 1
	return ptc

## udocID --> ldocID
def build_u2l():
	u2l = {}
	if not os.path.exists('cache/u2l.pkl'):
		u2l = {mdoc['udocID']: mdoc['ldocID'] for mdoc in db['docs'].find()}
		pickle.dump(u2l, open('cache/u2l.pkl', 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		u2l = pickle.load(open('cache/u2l.pkl', 'rb'))
	return u2l

## total word count
## pat (lower) --> udocID --> patcount
def build_PWC(min_count, min_df, training_udocIDs):

	fn = 'cache/PWC.'+str(min_count)+'.'+str(min_df)+'.pkl'

	if not os.path.exists(fn) or overwrite:
		PWC = defaultdict(Counter)
		for udocID in range(40000):
			ptc = word_counter(udocID)
			for p in ptc:
				PWC[p][udocID] += 1

		## pruning
		pruned = {}
		for p in PWC:
			## min count
			occurring = [PWC[p][uid] for uid in PWC[p] if uid in training_udocIDs]
			if len(occurring) < min_df: continue
			elif sum(occurring) < min_count: continue
			else:
				pruned[p] = dict(PWC[p])
		pickle.dump(pruned, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		PWC = pickle.load(open(fn, 'rb'))
	return PWC

def build_nt(PWC, training_udocIDs):
	fn = 'cache/PatN.pkl'
	if not os.path.exists(fn):
		N = {}
		for p in PWC:
			count_sequence_of_t_in_training_set = [PWC[p][uid] for uid in PWC[p] if uid in training_udocIDs]
			N[p] = mathutil.entropy(count_sequence_of_t_in_training_set)
		pickle.dump(N, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		N = pickle.load(open(fn, 'rb'))
	return N

def build_K(): # cardinality of |d|, i.e., K|d|
	fn = 'cache/PatK.pkl'
	if not os.path.exists(fn):
		K = {} # udocID --> K|d|: length of document d
		for udocID in range(40000):
			K[udocID] = sum([mdoc['sent_length'] for mdoc in db['sents'].find({'udocID':udocID})])
		pickle.dump(K, open(fn, 'wb'), pickle.HIGHEST_PROTOCOL)
	else:
		K = pickle.load(open(fn, 'rb'))
	return K

def create_training(PWC, D, training_udocIDs, tf_type, idf_type, min_count, min_df):
	fn = 'cache/TF'+tf_type+'x'+'IDF'+idf_type

	fn = fn + '.pat.'+str(min_count)+'.'+str(min_df)+'.train.pkl'

	K_values_in_training = [K[uid] for uid in K if uid in training_udocIDs]
	delta_d = float(sum(K_values_in_training)/float(len(K_values_in_training))) # average document length, ignore testing docs
	max_nt = max(N.values())

	if not os.path.exists(fn):
		training_TFIDF = defaultdict(Counter)
		for udocID in training_udocIDs:
			## training data
			ptc = word_counter(udocID)
			for p in ptc:

				if p not in PWC: continue

				if tf_type == '1':
					tf = 1+math.log(ptc[p],2)  # tf1
				elif tf_type == '3':
					tf = ptc[p]/float( ptc[p] + K[udocID]/delta_d )
				else:
					tf = False
					print 'invalid tf_type'
					exit(0)

				if idf_type == '1':
					# idf1
					Ft = len([uid for uid in PWC[p] if uid in training_udocIDs]) # only count documents in training
					idf = D/float(Ft) 
				elif idf_type == '2':
					idf = max_nt - N[p]
				else:
					idf = False
					print 'invalid idf_type'
					exit(0)

				tfidf = tf*idf
				training_TFIDF[p][udocID] = tfidf

		pickle.dump(training_TFIDF, open( fn, 'wb'), pickle.HIGHEST_PROTOCOL)

def create_testing(PWC, D, testing_udocIDs, tf_type, idf_type):
	fn = 'cache/TF'+tf_type+'x'+'IDF'+idf_type
	fn = fn + '.pat.'+str(min_count)+'.'+str(min_df)+'.test.pkl'


	K_values_in_training = [K[uid] for uid in K if uid not in testing_udocIDs]
	delta_d = float(sum(K_values_in_training)/float(len(K_values_in_training))) # average document length, ignore testing docs
	max_nt = max(N.values())

	if not os.path.exists(fn):
		testing_TFIDF = defaultdict(Counter)
		for udocID in testing_udocIDs:
			## training data
			ptc = word_counter(udocID)
			for p in ptc:
				if tf_type == '1':
					tf = 1+math.log(ptc[p],2) # tf1
				elif tf_type == '3':
					tf = ptc[p]/float( ptc[p] + K[udocID]/delta_d )
				else:
					tf = False
					print 'invalid tf_type'
					exit(0)

				if idf_type == '1': # idf1
					if p in PWC:
						Ft = len([uid for uid in PWC[p] if uid in training_udocIDs])
						idf = D/float(Ft) 						
					else:
						idf = 1/D # idf1
				elif idf_type == '2': # idf2
					idf = max_nt - N[p]
				else:
					idf = False
					print 'invalid idf_type'
					exit(0)

				tfidf = tf*idf
				testing_TFIDF[p][udocID] = tfidf
		pickle.dump(testing_TFIDF, open( fn, 'wb'), pickle.HIGHEST_PROTOCOL)

## change  word --> udocID --> wc
##     to  udocID --> word --> wc
def inverse_key(TFIDF):
	inversed = defaultdict(dict)
	for p in TFIDF:
		for udocID in TFIDF[p]:
			tfidf = TFIDF[p][udocID]
			inversed[udocID][p] = tfidf
	return inversed

if __name__ == '__main__':

	tf_type = sys.argv[1]
	idf_type = sys.argv[2]


	overwrite = True if '--overwrite' in sys.argv else False
	min_count = 5
	min_df = 3

	print 'overwrite:', overwrite
	print 'tf:', tf_type
	print 'idf:', idf_type
	print '='*100
	raw_input()

	print 'build u2l and get testing/training udocID'
	u2l = build_u2l()
	testing_udocIDs  = set([x for x in u2l if u2l[x] >= 800])
	training_udocIDs = set([x for x in u2l if u2l[x] < 800])

	print 'build PWC'
	PWC = build_PWC(min_count, min_df ,training_udocIDs)

	print 'build K'
	K = build_K()


	
	print 'build N'
	N = build_nt(PWC, training_udocIDs)

	print 'create training'
	training_TFIDF = create_training(PWC, D, training_udocIDs, tf_type, idf_type, min_count, min_df)

	print 'create testing'
	testing_TFIDF  = create_testing(PWC, D,  testing_udocIDs,  tf_type, idf_type, min_count, min_df)

