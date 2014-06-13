# combine binary classifier probibility

sid = "538bcfaad4388c59136665df"
param = 'c2g0.001t2'

cols = []

# for i in range(40):
# 	# 1.b.c2g0.001t2.p.out
# 	# 1.b.gold
# 	gold_fn = str(i)+'.b.gold'
# 	out_fn = str(i)+'.b.'+param+'.p.out'

# 	col = map(lambda x:x.strip().split()[1], open('tmp/'+sid+'/'+out_fn).read().strip().split('\n')[1:])
# 	cols.append(col)


def load(sid, param, prob):
	# 0.b.default.out
	# 0.b.gold
	root = 'tmp/'+sid
	if prob:
		related_files = [x for x in os.listdir(root) if x.endswith(param+'.p.out') or x.endswith('.gold')]
	else:
		related_files = [x for x in os.listdir(root) if x.endswith(param+'.out') or x.endswith('.gold')]

	out_files = [x for x in related_files if x.endswith('.out')]
	gold_files = [x for x in related_files if x.endswith('.gold')]

	if len(out_files) == 0:
		print 'no output files'
		return False

	Res = {}

	## load gold
	gold_label_in_eids = []
	for gold_file in gold_files:
		eid = gold_file.split('.')[0] # gold_file: "0.b.gold"
		gold_label_in_eid = [eid if x == '+1' else False for x in open(os.path.join(root,gold_file) ).read().strip().split('\n')]
		gold_label_in_eids.append(gold_label_in_eid)

	# list of eids: [0,0,....,1,..1,...39,39,...39]
	gold_labels = [reduce(lambda a,b:a or b, x) for x in zip(*gold_label_in_eids)]

	out_files = sorted(out_files, key=lambda x:int(x.split('.')[0]))

	predictions = []
	for out_file in out_files:
		eid = out_file.split('.')[0] # out_file: "0.b.default.out", eid: '0'

		if not prob:
			prediction = open(os.path.join(root,out_file) ).read().strip().split('\n')
		else:
			prediction = map(lambda x:x.split()[1], open(os.path.join(root,out_file) ).read().strip().split('\n')[1:])

		predictions.append(prediction)
	predict_labels = zip(*predictions)

	prediction_results = zip(gold_labels, predict_labels)
	return prediction_results

# kw-TF3xIDF2	{ "_id" : ObjectId("538bcfaad4388c59136665df"), "keyword_type" : "extend", "lemma" : true, "TFIDF_type" : "TF3xIDF2", "feature_name" : "keyword_TFIDF" }
# kw-emo-s-50%	[score] cut 50, min_count 4, -frequency (538a1df3d4388c32be4c2c9b)
# kw-bag	extend, lemma (537451d1d4388c7843516ba4)
# kw-emo-s-50%	[score] cut 50, min_count 4, -frequency (538a1df3d4388c32be4c2c9b)

def fusion(systems, weight):



if __name__ == '__main__':
	
	prob = True

	candidate = [
		("538bcfaad4388c59136665df", 'c2g0.001t2', 0.5), 
		("538a1df3d4388c32be4c2c9b", '', 0)
	]
	
	queue = []
	for sid, param in zip(sids, params):
		R = load(sid, param, prob)
		queue.append(R)


