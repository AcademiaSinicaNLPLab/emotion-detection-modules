# -*- coding: utf-8 -*-

import sys
sys.path.append('pymodules')

import color
import pickle, os
import logging
from collections import defaultdict


## input: dictionary of (emotion, value)
## output: dictionary of (emotion, 1) for emotions passed the threshold
def accumulate_threshold(count, percentage):
	## temp_dict -> { 0.3: ['happy', 'angry'], 0.8: ['sleepy'], ... }
	## (count)	    { 2:   ['bouncy', 'sleepy', 'hungry', 'creative'], 3: ['cheerful']}
	temp_dict = defaultdict( list ) 
	for e in count:
		temp_dict[count[e]].append(e)
	
	## temp_list -> [ (0.8, ['sleepy']), (0.3, ['happy', 'angry']), ... ] ((sorted))
	## (count)	    [ (3, ['cheerful']), (2,   ['bouncy', 'sleepy', 'hungry', 'creative'])]
	temp_list = temp_dict.items()
	temp_list.sort(reverse=True)

	th = percentage * sum( count.values() )
	current_sum = 0
	selected_emotions = []

	while current_sum < th:
		top = temp_list.pop(0)
		selected_emotions.extend( top[1] )
		current_sum += top[0] * len(top[1])

	return dict( zip(selected_emotions, [1]*len(selected_emotions)) )


def pattern_scoring_function(pat_counts):

	score = {}
	for anchor in pat_counts:

		SUM = float( sum( [ pat_counts[category] for category in pat_counts if category != anchor ] ) )
		SUMSQ = float( sum( [ (pat_counts[category] ** 2) for category in pat_counts if category != anchor ] ) )
		
		anchor_value = float( pat_counts[anchor] )
		not_anchor_value = float( SUMSQ/( SUM + 0.9 ** SUM ) )
		
		score[anchor] = anchor_value / (anchor_value + not_anchor_value)

	return score

