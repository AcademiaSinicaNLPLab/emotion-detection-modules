# -*- coding: utf-8 -*-
import sys, mathutil, math, json, pickle
import matplotlib.pyplot as plt
from collections import defaultdict

import pymongo

db = pymongo.Connection('doraemon.iis.sinica.edu.tw')['LJ40K']

def get_pat_count_dist(pat):
	mdoc = db.lexicon.nested.find_one({'pattern': pat.lower()})
	return None if not mdoc else mdoc['count']

def get_pat_score(pat):
	mdoc = db.patscore.normal.find_one({'pattern': pat.lower()})
	db.lexicon.nested.find_one({'pattern': pat})
	return None if not mdoc else mdoc['score']

## step 1
## filter out bad patterns using count distribution

def filter_confidence_interval(v):
	return ''

def filter_entropy(v, threshold=5.2):
	ent = mathutil.entropy(v)
	return True if ent < threshold else False
	# return

def check_pattern_quality(pat):
	dist = get_pat_count_dist(pat.lower())
	

def scale_max(v): return [x/float(max(v)) for x in v]
	
def Mm(scaled_v):
	mean = mathutil.avg(scaled_v)
	return (1.0-mean)/mean

def std(v):
	return mathutil.standard_deviation(v)
## step 2
## pattern scoring

def confidence_level(v):


if __name__ == '__main__':
	import json
	pat_counts = json.load(open('pat_counts.json'))

	collect = []

	for pat, count in pat_counts:

		dist = get_pat_count_dist(pat)

		v = dist.values()

		scaled_v = scale_max(v)

		keep = filter_entropy(v)

		mdoc = {
			'pattern': pat,
			'count': count,

			'std': std(v),
			'nstd': std(scaled_v),
			'Mm': Mm(scaled_v),
			'nstdxMm': std(scaled_v)*Mm(scaled_v),

			'confidence_level': 

		}

		if not keep: continue
		
		collect.append(pat)



		# raw_input()