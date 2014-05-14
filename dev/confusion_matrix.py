# -*- coding: utf-8 -*-
# import config
# import sys, pymongo, color

from collections import defaultdict, Counter
import json

### input
# file 1: gold		e.g., gold.txt
# file 2: answer	e.g., svm .out

### output
# matrix (std.out or file)

path_to_answer = '../tmp/0.out'
path_to_gold = '../tmp/gold.txt'

answers = [line.strip().split('\t')[0] for line in open(path_to_answer)]
golds = [line.strip().split('\t')[0] for line in open(path_to_gold)]
labels = { line.strip().split('\t')[0]:line.strip().split('\t')[-1] for line in open(path_to_gold) }

matrix = defaultdict(Counter)

for gold ,answer in zip(golds, answers):
	gold_label = labels[gold]
	gold_answer = labels[answer]
	matrix[gold_label][gold_answer] += 1


for gold_label in sorted(matrix.keys()):
	# sum([x[1] for x in matrix[gold_label].items()])
	print gold_label, sorted(matrix[gold_label].items(), key=lambda x:x[1], reverse=True)
	