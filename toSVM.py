## read from mongodb.features.xxx
## generate svm feature file

import config
import pymongo, sys
from collections import defaultdict

db = pymongo.Connection(config.mongo_addr)[config.db_name]



# use collection e.g., features.position
co_feature = db['features.'+setting['feature_type']]

# later used in getting emotion id
emotion_list = sorted([d['emotion'] for d in db['emotions'].find({'label': 'LJ40K'})])


## ------------------------ settings --------------------- ##
setting = {
	"section": "b20_m60_e20",
	"feature_type": "position",
	"f": 0,
	"c": 0
}

# get setting id
setting_id = str(db['features.settings'].find_one(setting)['_id'])
## ------------------------------------------------------- ##

feature_names = {} # global used because of multiple feature sets


def generate_vectors():

	vectors = defaultdict(list)

	for mdoc in co_feature.find({'setting': setting_id}):

		# skip if no feature extracted for the current doc
		if not mdoc['feature']:
			continue

		if type(mdoc['feature']) == dict:
			feature = mdoc['feature'].items()
		elif type(mdoc['feature']) == list:
			feature = mdoc['feature']
		else:
			print >> sys.stderr, '[error] cannot read feature with', type(mdoc['feature']) ,'type'
			exit(-1)

		## form the feature vector
		feature_vector = []
		for feature_name, feature_value in feature:

			# get feature id
			if feature_name in feature_names:
				fid = feature_names[feature_name]
			else:
				fid = len(feature_names)
				feature_names[feature_name] = fid

			# store as the form 1:100
			feature_vector.append( ( fid, feature_value) )

		# feature indices must be in an ascending order
		feature_vector.sort(key=lambda x:x[0])

		# ready to generate plain text feature vector
		feature_vector = [str(fid)+':'+str(feature_value) for (fid, feature_value) in feature_vector]

		# put the gold answer at the first place
		feature_vector.insert(0, str(emotion_list.index(mdoc['emotion'])) )

		# toString
		# 3 0:2.768 1:1.909 2:1.46201119074 3:6.365 4:3.641 5:2.166 ...
		feature_vector = ' '.join(feature_vector)

		vectors[ mdoc['emotion'] ].append( (mdoc['udocID'], feature_vector) )
	
	return vectors

def generate_test_train_files(vectors, train_out='train.txt', test_out='test.txt', gold_out='gold.txt'):

	fw_train = open(train_out, 'w')
	fw_test = open(test_out, 'w')
	fw_gold = open(gold_out, 'w')

	# default: [800:200]
	# p = 0
	for e in vectors:
		vector = sorted(vectors[e], key=lambda x:x[0])
		train, test = vector[:800], vector[800:]

		train_txt = '\n'.join([x[1] for x in train])
		test_txt = '\n'.join([x[1] for x in test])
		gold_txt = '\n'.join([x[0] for x in test])


		fw_train.write(train_txt + '\n')
		fw_test.write(test_txt + '\n')
		fw_gold.write(gold_txt + '\n')

	fw_train.close()
	fw_test.close()
	fw_gold.close()

if __name__ == '__main__':

	vectors = generate_vectors()

	generate_test_train_files(vectors)



