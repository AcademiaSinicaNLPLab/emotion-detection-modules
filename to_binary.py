import os, color, sys
from collections import Counter, defaultdict
import random

POSITIVE_LABEL = '+1'
NEGATIVE_LABEL = '-1'

def load_src_files(src_paths):
	data = {}
	for ftype, src_path in src_paths.items():
		v = []
		for line in open(src_path):
			line = line.strip().split(' ')
			label, feature = line[0], line[1:]
			v.append( (label, feature) )
		data[ftype] = v
	return data

def to_binary(data, anchor):

	binary_data = {}
	for ftype in data:
		positive, negative = [], []

		binary_labeled_feature = []
		candidate_idx = []  # for train only
		for (i, (label, feature)) in enumerate(data[ftype]):
			if label == anchor:
				new_label = POSITIVE_LABEL
			else:
				new_label = NEGATIVE_LABEL
				candidate_idx.append(i) # for train only
			binary_labeled_feature.append( [new_label] + feature )


		if ftype == 'train':
			# randomly generate 800 idx in negative
			random.shuffle(candidate_idx)
			selected_idx = set(candidate_idx[:800])
			# collect POSITIVE + selected NEGATIVE
			balanced = []
			for i in range(len(binary_labeled_feature)):
				new_label = binary_labeled_feature[i][0]

				if new_label == POSITIVE_LABEL:
					balanced.append(binary_labeled_feature[i])
				elif new_label == NEGATIVE_LABEL and i in selected_idx:
					balanced.append(binary_labeled_feature[i])
				else: ## new_label == NEGATIVE_LABEL and i not in selected_idx
					continue
			binary_labeled_feature = balanced

		binary_data[ftype] = binary_labeled_feature

	return binary_data

def dest_files_exist(sid, root):
	for ftype in ['train', 'test', 'gold']:
		for anchor in range(40):
			dest_fn = '.'.join([str(anchor), 'b', ftype])
			dest_path = os.path.join(root, dest_fn)
			if not os.path.exists(dest_path):
				return False
	return True

def run(sid):
	c = Counter()
	root = os.path.join('tmp', sid)
	if not os.path.exists(root): os.makedirs(root)
	
	src_paths = {}
	for ftype in ('train', 'test', 'gold'):
		src_fn = '.'.join([sid,ftype,'txt'])
		src_path = os.path.join('tmp', src_fn)
		if not os.path.exists(src_path):
			print 'missing', src_path, 'run toSVM.py before transforming to binary'
			exit(-1)

		src_paths[ftype] = src_path

	if dest_files_exist(sid, root):
		exit(0)

	## load source files
	data = load_src_files(src_paths)

	## get all labels
	labels = set([x[0] for x in data['train']])

	for anchor in labels: # for each gold label, transform to binary
		
		binary_data = to_binary(data, anchor)

		print 'generating binary data for label', color.render(str(anchor), 'g')

		for ftype in data:

			dest_fn = '.'.join([anchor, 'b', ftype])
			dest_path = os.path.join(root, dest_fn)

			binary_labeled_feature = binary_data[ftype]

			with open(dest_path, 'w') as fw:
				for line_list in binary_labeled_feature:
					line_str = ' '.join(line_list) + '\n'
					fw.write(line_str)

if __name__ == '__main__':

	# sid = '53875c80d4388c4100cac5b2'
	sid = sys.argv[1].strip()
	run(sid)

