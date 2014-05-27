# -*- coding: utf-8 -*-

import config, color
import os, sys, re
import subprocess
from collections import defaultdict
import logging

## 1. given a setting_id
## 2. setup svm options
## 3. file status check
##		determine what stage of the current setting
## 4. run svm-train 
## 		input:  training text (.txt)
##		output: model file (.m)
## 5. run svm-predict
## 		input: 	testing text (.txt)
## 				model file (.m)
##		output:	predict output (.out)

cores = 1
quiet_mode = False
scale_mode = False

def check(setting_id):
	return True if re.findall(r'^([a-z0-9]{24})$', str(setting_id).strip()) else False

def parse_params(str_params):
	# target forms: ["-c 4 -b 1", "-c 4-b1", "-c4 -b1", "c4b1", "c4 b1", "c4 b 1", "-n 0.5"]
	return [] if str_params == 'default' else sorted( re.findall(r'-?([a-z])\s*([0-9\.]+)', str_params), key=lambda x:x[0] )

def get_files_info(setting_id, str_svm_params, svm_file_root='tmp'):

	module_path = os.path.dirname(os.path.abspath(__file__))

	# scale = '' if not scale_mode else 'scale'
	train_test_ext = 'txt'

	files = {
		'train'	: {'name': '.'.join([setting_id, 'train', 		train_test_ext]) },
		'test' 	: {'name': '.'.join([setting_id, 'test',  		train_test_ext]) },
		'model'	: {'name': '.'.join([setting_id, str_svm_params, 'm']) },
		'output': {'name': '.'.join([setting_id, str_svm_params, 'out']) }
	}
	for ftype in files:
		files[ftype]['status'] = os.path.exists( os.path.join( svm_file_root, files[ftype]['name'] ) )
		files[ftype]['path']   = os.path.join(module_path, svm_file_root, files[ftype]['name'])
	return files


## workflow = [
##		[ <libsvm_path>/svm-train,		svm-params,		<setting_id>.train.txt,		<setting_id>.<model_params>.m  									],
##		[ <libsvm_path>/svm-predict 	svm-params,		<setting_id>.test.txt,		<setting_id>.<model_params>.m, <setting_id>.<model_params>.out 	],
##	]

def create_workflow(files, svm_params):

	workflow = []

	# svm_params: [('b', '1'), ('c', '5'), ('n', '0.5')]
	# svm_param_args: ['-b', '1', '-c', '5', '-n', '0.5']
	svm_param_args = [] if not svm_params else list(reduce(lambda x,y:x+y, map(lambda x:('-'+x[0],x[1]), svm_params)))

	## train(o), test(x) or train(x), test(o) or train(x), test(x)
	if not files['train']['status'] or not files['test']['status']:
		logging.error("Can't find train or test files")
		exit(-1)

	## train(o), test(o), model(o), output(o)
	elif files['train']['status'] and files['test']['status'] and files['model']['status'] and files['output']['status']:
		logging.info("All train/test tasks are done: do nothing!")

	### both need test
	else:
		## args for test
		test_args =  [os.path.join(config.libsvm_path, config.libsvm_program['test'])]
		test_args += ['-b', '1'] if ('b', '1') in svm_params else []
		test_args += [files['test']['path'], files['model']['path'], files['output']['path']]	
			
		## train(o), test(o), model(x), output(x)
		if files['train']['status'] and files['test']['status'] and not files['model']['status']:
			logging.info("No model files, train first then test")

			## args for train
			if quiet_mode:
				svm_param_args.insert(0, '-q')

			train_args =  [os.path.join(config.libsvm_path, config.libsvm_program['train'])]
			train_args += svm_param_args
			train_args += [files['train']['path'], files['model']['path']]

			workflow = [ train_args, test_args ]

		## train(o), test(o), model(o), output(x)
		elif files['train']['status'] and files['test']['status'] and files['model']['status'] and not files['output']['status']:
			logging.info("No output files, test only")
			workflow = [ test_args ]

		else: # WTF?!
			logging.error('invalid files')
			workflow = False

	return workflow

def show_confirm(workflow):
	for cmd in workflow:
		print >> sys.stderr, color.render('[cmd]', 'lc'), ' '.join(cmd)
	print >> sys.stderr, color.render('> correct? [Y/n] ', 'g'),
	ok = raw_input()
	print >> sys.stderr
	return ok

def execute_workflow(workflow):
	for cmd in workflow:
		print >> sys.stderr, color.render('['+cmd[0].split('/')[-1]+']', 'r')
		print >> sys.stderr, color.render(' start '+'>'*10, 'y' )
		retcode = subprocess.call(cmd, shell=False)
		print >> sys.stderr, color.render( ' end '+'<'*10, 'b')	
	return True

def main(setting_id, svm_params=[]):

	## str_svm_params: looks like "default" or "b1c4"
	## the options string will be in the ascending alphabet order after runing parse_params(), e.g., b1c4
	## used for checking "5371bc38d4388c470a7fb71f.b1c4.m" and "5371bc38d4388c470a7fb71f.b1c4.out"
	str_svm_params = 'default' if not svm_params else ''.join( [k+v for k,v in svm_params ] )	

	files = get_files_info(setting_id, str_svm_params, svm_file_root=config.svm_file_root)

	## create workflow for svm training/testing
	workflow = create_workflow(files, svm_params)
	
	## prompt workflow messages
	if workflow == False:
		logging.error('invalid files')
		exit(-1)
	elif len(workflow) == 0:
		exit(0)
	else:
		# confirm message
		ok = show_confirm(workflow)

		if ok.lower().startswith('n'):
			exit(0)
		else:
			if cores > 1:
				multicore = 'export OMP_NUM_THREADS='+str(cores)
				subprocess.call([multicore], shell=True)

			execute_workflow(workflow)

if __name__ == '__main__':

	import getopt

	add_opts = [
		('setting_id', ['<setting_id>: specify a setting ID (e.g., 537086fcd4388c7e81676914)', 
					   '           which can be retrieved from the mongo collection features.settings' ]),
		('--quiet', 	['--quiet: run svm in quiet mode']), 
		('--core', 		['-c, --core: multi-core for svm']), 
		('--param', 	['--param: parameter string for libsvm (e.g., use "c4b1" or "-c 4 -b 1" to represent the libsvm parameters -c 4 -b 1)'])		
	]

	arg_idx = 2 if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 1
	try:
		opts, args = getopt.getopt(sys.argv[arg_idx:],'hvop:q',['help', 'verbose', 'overwrite', 'list', 'param=','multi=', 'quiet'])
		setting_id = sys.argv[1].strip()
	except:
		config.help('run_svm', addon=add_opts, args=['<setting_id>'], exit=2)


	svm_params = []
	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('run_svm', addon=add_opts)
		elif opt in ('-q','--quiet'): quiet_mode = True
		elif opt in ('-s','--scale'): scale_mode = True
		elif opt in ('-p','--param'): svm_params = parse_params(arg.strip())
		elif opt in ('--multi'): cores = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True

	## set log level
	loglevel = logging.DEBUG if config.verbose else logging.INFO
	logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)


	valid = check(setting_id)
	if not valid:
		logging.error('invalid setting_id')
		exit(-1)

	main(setting_id, svm_params)







