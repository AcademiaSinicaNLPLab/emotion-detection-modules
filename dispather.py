from itertools import product

core = 4

params = [
	'default',
	'c9r5t1',
	'c9t2',
	'c2t2',
	'c4t2',
	'c2g0.001t2', 
	'c2g0.01t2', 
	'c9g0.01t2',
	'c9g0.005t2',
	'c9g0.001t2',
	'c9g0.0005t2',
	'c9g0.0001t2'
]

sids = [
	'538a08a5d4388c142389a032',
	'538a128cd4388c32c05231e8',
	'538a1df3d4388c32be4c2c9b',
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

if __name__ == '__main__':

	import subprocess
	# sids, params = list(set(sids)), list(set(params))

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
				# subprocess.call(['python','evaluate_binary.py',sid,param])
				# print sid, param
				# raw_input()
		
		print 'save',fn

		subprocess.call(['chmod','+x',fn])
