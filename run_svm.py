# -*- coding: utf-8 -*-

import config, color
import os, sys, re
import subprocess
from collections import defaultdict

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


# -------------------------------------------- config --------------------------------------------------- #

cores = 1

setting_id = None

## <bool> for display all available setting id and corresponding files
list_availabel_settings = False

# libsvm abs path
libsvm_path  = '/tools/libsvm'

libsvm_program = {
	'train':'svm-train',
	'test': 'svm-predict',
	'check': 'tools/checkdata.py',
}

## setup libsvm parameters
libsvm_params = []

# current model abs path
# this program will operate all train, test, model, out files locally
module_path = os.path.dirname(os.path.abspath(__file__))

# relative file pathes for train, test, model and out
file_root = 'tmp'
file_root_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_root)

## for naming a default svm setting
model_params = 'default'

files = {}
sids = defaultdict(list)
# ---------------------------------------------------------------------------------------------------- #

def parse_params(str_params):
	# target forms: ["-c 4 -b 1", "-c 4-b1", "-c4 -b1", "c4b1", "c4 b1", "c4 b 1", "-n 0.5"]
	return sorted( re.findall(r'-?([a-z])\s*([0-9\.]+)', str_params), key=lambda x:x[0] )

## grouping available setting ids and corresponding files
def grouping(display=False):
	global sids
	if len(sids) == 0:
		for fn in os.listdir(file_root):
			sid = re.findall(r'^([a-z0-9]{24})', fn)
			if sid: sids[sid[0]].append(fn)

	if display:
		print >> sys.stderr, '='*50	
		for sid in sids:
			print >> sys.stderr, '>', sid
			for fn in sids[sid]:
				print >> sys.stderr, '\t-',fn
		print >> sys.stderr, '='*50

## prompt until obtain a valid setting id
def setup_setting_id():
	global setting_id
	while True:
		if not setting_id: # setteing_id is empty
			grouping(display=True)
			print >> sys.stderr, '> choose a setting_id: ',
			setting_id = raw_input().strip()
		elif setting_id and not re.findall(r'^([a-z0-9]{24})$', str(setting_id).strip()): # invalid setting id
			grouping(display=True)
			print >> sys.stderr, '> choose a valid setting_id: ',
			setting_id = raw_input().strip()
		else:
			break
	print >> sys.stderr

## restore svm parameters
## e.g.,
## input: 'b1c4'
## return: ['-b', '1', '-c', '4']
def restore(model_params):
	return list(reduce(lambda x,y: x+y, [('-'+k,v) for (k,v) in re.findall( r'(\w)(\d)', model_params.strip() )]))

## workflow = [
##		[ <libsvm_path>/svm-train,		svm-params,		<setting_id>.train.txt,		<setting_id>.<model_params>.m  									],
##		[ <libsvm_path>/svm-predict 	svm-params,		<setting_id>.test.txt,		<setting_id>.<model_params>.m, <setting_id>.<model_params>.out 	],
##	]
## svm-params: -c 4 -b 1
def create_workflow(files, model_params):

	workflow = []

	## status: {'test': True, 'output': False, 'model': False, 'train': True}
	status = { ftype: os.path.exists( os.path.join( file_root, files[ftype] ) ) for ftype in files }
	
	## params_list: ['-b', '1', '-c', '4']
	params_list = [] if model_params == 'default' else restore(model_params)

	## absolute pathes for files
	abs_pathes = { ftype: os.path.join(module_path, file_root, files[ftype]) for ftype in files }
	
	if status['output']: # output exists
		# do nothing
		pass

	elif not status['output']: # no output

		train_args = [ os.path.join(libsvm_path, libsvm_program['train']) ]
		train_args += params_list
		train_args += [ abs_pathes['train'], abs_pathes['model'] ]

		test_args =  [ os.path.join(libsvm_path, libsvm_program['test']) ]
		test_args += ['-b', '1'] if 'b1' in model_params else []
		test_args += [ abs_pathes['test'], abs_pathes['model'], abs_pathes['output'] ]

		# with model --> svm-predict only
		if status['model']:
			workflow = [ test_args ]
		# without model --> svm-train + svm-predict
		else: 
			workflow = [ train_args, test_args ]

	else: # WTF?!
		workflow = False

	return workflow

if __name__ == '__main__':

	import getopt

	add_opts = [
		('setting_id', ['<setting_id>: specify a setting ID (e.g., 537086fcd4388c7e81676914)', 
					   '           which can be retrieved from the mongo collection features.settings' ]),
		('--list', 		['--list: list local available setting IDs and related files']), 
		('--core', 		['-c, --core: multi-core for svm']), 
		('--param', 	['--param: parameter string for libsvm (e.g., use "c4b1" or "-c 4 -b 1" to represent the libsvm parameters -c 4 -b 1)'])		
	]

	arg_idx = 2 if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 1
	try:
		opts, args = getopt.getopt(sys.argv[arg_idx:],'hvo',['help', 'verbose', 'overwrite'])
		setting_id_str = sys.argv[1].strip()
	except:
		config.help('run_svm', addon=add_opts, args=['<setting_id>'], exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('run_svm', addon=add_opts)
		elif opt in ('--list'): list_availabel_settings = True
		elif opt in ('--param'): libsvm_params = parse_params( arg.strip() )
		elif opt in ('--multi'): cores = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True

	## group files by setting_id
	grouping(display=list_availabel_settings)
	if list_availabel_settings:
		exit(1)

	## check setting id
	setup_setting_id()

	# setup_param()

	## model params: looks like "default" or "b1c4"
	## the options string will be in the ascending alphabet order after runing parse_params(), e.g., b1c4
	## used in checking "5371bc38d4388c470a7fb71f.b1c4.m" and "5371bc38d4388c470a7fb71f.b1c4.out"
	if libsvm_params:
		model_params = ''.join( [k+v for k,v in libsvm_params ] )

	files = {
		'train'	: '.'.join([setting_id, 'train', 		'txt']),
		'test' 	: '.'.join([setting_id, 'test', 		'txt']),
		'model'	: '.'.join([setting_id, model_params, 	'm']),
		'output': '.'.join([setting_id, model_params, 	'out'])
	}

	## create workflow for svm training/testing
	workflow = create_workflow(files, model_params)
	
	## prompt workflow messages
	if workflow == False:
		print >> sys.stderr, '[error] validate the files:','\n',files
		exit(-1)
	elif len(workflow) == 0:
		# grouping(display=True)
		print >> sys.stderr, '[info] All train/test tasks are done!'
		print >> sys.stderr, '[info] Related files:'
		for fn in files.values():
			print >> sys.stderr, '       -', fn
		exit(0)

	# confirm message
	for cmd in workflow:
		print >> sys.stderr, color.render('[cmd]', 'lc'), ' '.join(cmd)
	print >> sys.stderr, color.render('> correct? [Y/n] ', 'g'),
	ok = raw_input()
	print >> sys.stderr

	if ok.lower().startswith('n'):
		exit(-1)
	else:
		if cores > 1:
			multicore = 'export OMP_NUM_THREADS='+str(cores)
			subprocess.call([multicore], shell=True)

		for cmd in workflow:
			print >> sys.stderr, color.render('['+cmd[0].split('/')[-1]+']', 'r')
			print >> sys.stderr, color.render(' start '+'>'*10, 'y' )
			retcode = subprocess.call(cmd, shell=False)
			print >> sys.stderr, color.render( ' end '+'<'*10, 'b')


