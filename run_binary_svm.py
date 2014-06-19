import config
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

		subprocess.call(train_cmd, shell=False)
		subprocess.Popen(test_cmd, stdout=subprocess.PIPE, shell=False) ## use stdout=subprocess.PIPE to prevent accuracy output
		
		print 'processing', eid, '(',i+1, '/', len(eids), ')'

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

	if complete == len(eids) and not config.overwrite:
		return False
	else:
		return 	files


if __name__ == '__main__':

	# sid = '53875c80d4388c4100cac5b2'
	# param = 'default'

	if '--help' in sys.argv or '-h' in sys.argv:
		print ' '.join(['Usage: python',__file__,'<sid>','<param>','[-p or --prob]'])
		exit(0)

	if '--overwrite' in sys.argv:
		config.overwrite = True
	else:
		config.overwrite = False
		

	sid = sys.argv[1].strip()
	param = sys.argv[2].strip()

	if '-p' in sys.argv or '--prob' in sys.argv: prob = True
	else: prob = False

	todo_files = check_files(sid, param, prob)

	if not todo_files: ## all done
		print '>> all done!'
	else:
		svm_binary(sid, param, prob, todo_files)
