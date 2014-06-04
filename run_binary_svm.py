import os, subprocess, re, pickle, color, sys
from pprint import pprint


def parse_params(str_params):
	# target forms: ["-c 4 -b 1", "-c 4-b1", "-c4 -b1", "c4b1", "c4 b1", "c4 b 1", "-n 0.5"]
	return [] if str_params == 'default' else sorted( re.findall(r'-?([a-z])\s*([0-9\.]+)', str_params), key=lambda x:x[0] )

def svm_binary(sid, param, prob, files):

	## parse parameters
	svm_params = parse_params(param)
	training_args = [] if not svm_params else list(reduce(lambda x,y:x+y, map(lambda x:('-'+x[0],x[1]), svm_params)))

	eids = map(lambda x:str(x), sorted([int(x.split('.')[0]) for x in os.listdir('tmp/'+sid) if x.endswith('.b.gold')]) )
	# res = {}

	train_program = '/tools/libsvm/svm-train'
	test_program = '/tools/libsvm/svm-predict'

	# if files:
	for i, eid in enumerate(files.keys()):
		train_fn  = files[eid]['train']
		test_fn   = files[eid]['test']
		model_fn  = files[eid]['model']
		output_fn = files[eid]['output']

		train_cmd = [train_program, '-q']
		if prob: train_cmd += ['-b', '1']
		train_cmd += training_args + [train_fn, model_fn]

		test_cmd = [test_program]
		if prob: test_cmd += ['-b', '1']
		test_cmd += [test_fn, model_fn, output_fn]

		# print train_cmd
		# print test_cmd

		subprocess.call(train_cmd, shell=False)
		subprocess.Popen(test_cmd, stdout=subprocess.PIPE, shell=False) ## use stdout=subprocess.PIPE to prevent accuracy output

		print 'processing', eid, '(',i+1, '/', len(eids), ')'
		# print '-'*60
		# print
	# else:
	# 	# with open('tmp/'+sid+'/default.res', 'w') as fw:
	# 	for eid in eids:

	# 		train_fn  = 'tmp/'+sid+'/'+eid+'.b.train'
	# 		test_fn   = 'tmp/'+sid+'/'+eid+'.b.test'
	# 		model_fn  = 'tmp/'+sid+'/'+eid+'.b.'+param+'.m'
	# 		output_fn = 'tmp/'+sid+'/'+eid+'.b.'+param+'.out'




		
		# accuracy_str = proc.stdout.read().strip()
		# accuracy = float(re.findall(r'([0-9]+\.[0-9]+)%', accuracy_str)[0])
		# res[eid] = accuracy
		# fw.write(accuracy_str + '\n')

		# print eid, accuracy

	# print 'avg:', sum(res.values())/float(len(res.values())), '%'
	# pickle.dump(res, open('tmp/'+sid+'/'+param+'.pkl', 'w'))

def check_files(sid, param, prob):

	files = {}

	eids = map(lambda x:str(x), sorted([int(x.split('.')[0]) for x in os.listdir('tmp/'+sid) if x.endswith('.b.gold')]) )
	complete = 0
	for eid in eids:
		fns = {
			'train':  'tmp/'+sid+'/'+eid+'.b.train',
			'test':   'tmp/'+sid+'/'+eid+'.b.test',
			'model':  'tmp/'+sid+'/'+eid+'.b.'+param+'.m',
			'output': 'tmp/'+sid+'/'+eid+'.b.'+param+'.out'
		}
		if prob:
			fns['model'] = 'tmp/'+sid+'/'+eid+'.b.'+param+'.p.m'
			fns['output'] = 'tmp/'+sid+'/'+eid+'.b.'+param+'.p.out'

		if os.path.exists(fns['model']) and os.path.exists(fns['output']):
			complete += 1

		files[eid] = fns

	if complete == len(eids):
		return False
	else:
		return 	files
# def intersection(sid, param):

# 	import pymongo
# 	db = pymongo.Connection('doraemon.iis.sinica.edu.tw')['LJ40K']

# 	M2005 = [x['emotion'] for x in db['emotions'].find({'label':'Mishne05'})]
# 	LJ40K = [x['emotion'] for x in db['emotions'].find({'label':'LJ40K'})]
# 	eids = {x:i for i,x in enumerate(sorted(LJ40K))}
# 	# eid_to_emotion = {i:x for i,x in enumerate(sorted(LJ40K))}
# 	inter_emotions = [e for e in set(M2005+LJ40K) if e in M2005 and e in LJ40K]

# 	inter_eid_to_emotion = {}
# 	for e in inter_emotions:
# 		eid = eids[e]
# 		inter_eid_to_emotion[str(eid)] = e


# 	res = pickle.load(open('tmp/'+sid+'/'+param+'.pkl'))
# 	inter_res = [(inter_eid_to_emotion[eid], acc) for eid, acc in res.items() if eid in inter_eid_to_emotion]
	
# 	# map(lambda x: (inter_eid_to_emotion[x[0]],x[1]) )
# 	inter_res.sort(key=lambda x:x[0])

# 	inter_res = dict(inter_res)
# 	pprint(inter_res)
# 	print '='*50
# 	print 'avg (2005+LJ40K):', color.render(str( round( sum(inter_res.values())/float(len(inter_res.values())), 4)), 'y'), '%'


if __name__ == '__main__':

	# sid = '53875c80d4388c4100cac5b2'
	# param = 'default'

	sid = sys.argv[1].strip()
	param = sys.argv[2].strip()

	if '-p' in sys.argv or '--prob' in sys.argv: prob = True
	else: prob = False

	todo_files = check_files(sid, param, prob)


	if not todo_files: ## all done
		print '>> all done!'
		pass
	else:
		svm_binary(sid, param, prob, todo_files)
