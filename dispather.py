from itertools import product

core = 2

params = [
	'c2t2', 
	'c4t2', 
	'c9t2']

sids = [
	'53876afdd4388c03612805ae',
	'53876efbd4388c3e013e9272',
	'53875c80d4388c4100cac5b2',
	'53875eead4388c4eac581415',
	'53876645d4388c6f97360eb2',
	'538706fad4388c61c5deff2d',
	'53872b4ed4388c258c75b8e9',
	'5387635bd4388c34c92325f7',
	'538302743681df11cd509c77',
	'53877f0bd4388c6949626954',
	'53877105d4388c1adc151f73',
	'53877b0bd4388c37f6a22b1a',
	'53877ef0d4388c62c5619889']

def dispatcher(sids, params, core):
	dispatch = []
	step = len(sids)/core

	for i in range(core):
		if i == core - 1: dispatch.append(sids[i*step:])
		else: dispatch.append(sids[i*step:(i+1)*step])	

if __name__ == '__main__':

	import subprocess

	exe = dispatcher(sids, params, core)

	for fidx, sid_part in enumerate(exe):
		fn = str(fidx)+'.sh'
		with open(fn, 'w') as fw:

			for sid, param in product(sid_part, params):
				fw.write(' '.join(['python','run_binary_svm.py',sid,param]) + '\n')
				# print 
			for sid, param in product(sid_part, params):
				fw.write(' '.join(['python','evaluate_binary.py',sid,param]) + '\n')
		
		subprocess.call(['chmod','+x',fn])
