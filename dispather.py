import sys
import subprocess
from itertools import product

core = 1

params = [
	'default',
	'c9r5t1',
	
	#'c2t2',
	#'c4t2',
	'c9t2',

	'c2g0.001t2', 
	#'c2g0.01t2', 
	#'c9g0.01t2',
	#'c9g0.005t2',
	'c9g0.001t2',
	'c9g0.0005t2',
	'c9g0.0001t2'
]

sids = [
	'538be395d4388c4c7d533e2e', # pat-bag + kw-TF3xIDF2
	# '538bdc4cd4388c3b72ded9e7', # kw-TF3xIDF2 + pat-emo-s
	# '538be189d4388c7efe214736', # kw-TF1xIDF2 + pat-emo-s
	# '538be0edd4388c67c1d6950d', # kw-bag + kw-TF3xIDF2 + pat-emo-s
	# '538bcfaad4388c59136665df', # TF3xIDF2
	# '538bcf7ad4388c5190d8057c', # TF1xIDF2
	# '538b290cd4388c1eb95c3f7b', # kw-bag + pat-emo-s + kw-emo-s + pat-emo-s-pos
	# '538aeb10d4388c12a30803d9', # pat-emo-f-pos
	# '538ae979d4388c54633cf587', # pat-emo-b-pos
	# '538aec90d4388c49cb5c2705', # pat-emo-s-pos
	# "538a9256d4388c7d9203e92c", # pat-emo-s + kw-emo-s (538a9256d4388c7d9203e92c)
	# "538a9245d4388c7a1a54c294", # kw-bag + pat-emo-s + kw-emo-s (538a9245d4388c7a1a54c294)
	# '538a08a5d4388c142389a032',
	# '538a128cd4388c32c05231e8',
	# '538a1df3d4388c32be4c2c9b',
	# '53876afdd4388c03612805ae', # [b] cut 30, min_count 4, -frequency (53876afdd4388c03612805ae)
	# '53876efbd4388c3e013e9272', # [b] cut 50, min_count 4, -frequency (53876efbd4388c3e013e9272)
	# '5387fff3d4388c238838629f', # [freq] cut 50, min_count 4, -frequency (5387fff3d4388c238838629f)
	# '53875c80d4388c4100cac5b2', # [s] cut 30, min_count 4, -frequency (53875c80d4388c4100cac5b2)
	# '53875eead4388c4eac581415', # [s] cut 50, min_count 4, -frequency (53875eead4388c4eac581415)
	# '53876645d4388c6f97360eb2', # [s] cut 100, min_count 4, -frequency (53876645d4388c6f97360eb2)

	# '538706fad4388c61c5deff2d', # [b] cut 30, min_count 4, -frequency (538706fad4388c61c5deff2d)
	# '53872b4ed4388c258c75b8e9', # [b] cut 50, min_count 4, -frequency (53872b4ed4388c258c75b8e9)
	# '5387fdbcd4388c5d95b5be52', # [freq] cut 50, min_count 4, -frequency (5387fdbcd4388c5d95b5be52)
	# '5387635bd4388c34c92325f7', # [s] cut 30, min_count 4, -frequency (5387635bd4388c34c92325f7)
	# '538775cdd4388c2767c7dd92', # [s] cut 50, min_count 4, -frequency (538775cdd4388c2767c7dd92)

	# '537451d1d4388c7843516ba4', # extend, lemma (537451d1d4388c7843516ba4)
	# '537c6c90d4388c0e27069e7b', # min_count: 10 (537c6c90d4388c0e27069e7b)

	# '538302743681df11cd509c77', # kw-bag + pat-bag (538302743681df11cd509c77)
	# '53877f0bd4388c6949626954', # pat-emo-s + pat-emo-s-pos (53877f0bd4388c6949626954)
	# '53877105d4388c1adc151f73', # Fusion.a + pat-emo-s (53877105d4388c1adc151f73)
	# '53877b0bd4388c37f6a22b1a', # Fusion.a + pat-emo-s-pos (53877b0bd4388c37f6a22b1a)
	# '53877edfd4388c5ea47db964', # kw-bag + pat-emo-s (53877edfd4388c5ea47db964)
	# '53877ef0d4388c62c5619889', # kw-bag + pat-emo-s-pos (53877ef0d4388c62c5619889)
	# '53877f27d4388c70c7a72952'  # kw-bag + pat-emo-s + pat-emo-s-pos (53877f27d4388c70c7a72952)
]

def dispatcher(sids, params, core):
	dispatch = []

	sids_params = list(product(sids, params))
	step = len(sids_params)/core

	for i in range(core):
		if i == core - 1: dispatch.append(sids_params[i*step:])
		else: dispatch.append(sids_params[i*step:(i+1)*step])

	return dispatch

def show(sids, params, grouop_by):
	
	if grouop_by == 'row':
		sids_params = list(product(sids, params))
	elif grouop_by == 'col':
		sids_params = [(sid,param) for (param,sid) in list(product(params, sids))]
	else:
		return False
	
	for sid, param in sids_params:
		print sid, '\t', param
		subprocess.Popen(['python','evaluate_binary.py',sid,param], stdout=subprocess.PIPE)
		raw_input()

if __name__ == '__main__':

	if len(sys.argv) > 1:
		if sys.argv[1].strip() in ('row', 'col'): 
			grouop_by = sys.argv[1].strip()
			show(sids, params, grouop_by)
		else:
			print 'invalid argument, usage: python dispatcher.py [row/col]'
			exit(-1)

	else:
		dispatch = dispatcher(sids, params, core)
		used_sid_to_check_binary = set()		
		for fidx, sids_params in enumerate(dispatch):

			fn = str(fidx)+'.sh'
			with open(fn, 'w') as fw:

				for sid, param in sids_params:
					if sid not in used_sid_to_check_binary:
						used_sid_to_check_binary.add(sid)
						fw.write(' '.join(['python','to_binary.py',sid]) + '\n')

					fw.write(' '.join(['python','run_binary_svm.py',sid,param]) + '\n')

				for sid, param in sids_params:
					fw.write(' '.join(['python','evaluate_binary.py',sid,param]) + '\n')
			
			print 'save',fn

			subprocess.call(['chmod','+x',fn])
