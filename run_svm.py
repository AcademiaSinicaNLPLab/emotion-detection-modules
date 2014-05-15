
import config, color
import os, sys, re
import subprocess

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

## given setting id
setting_id = ''
# setting_id = '5371bc38d4388c470a7fb71f'
# setting_id = '537086fcd4388c7e81676914'

libsvm_path = '/Users/Maxis/tools/libsvm-3.17'

libsvm = {
	'train':'svm-train',
	'test': 'svm-predict',
	'check': 'tools/checkdata.py',
}

## setup libsvm parameters
libsvm_params = []
# libsvm_params = [('b', '1'), ('c', '4')]

file_root = 'tmp'

def get_to_do_list(related_files, model_params):

	files = {
		'train': False,
		'test': False,
		'model': False,
		'output': False,
	}

	for fn in related_files:

		## svm-predict output
		if fn.endswith(model_params+'.out'):
			files['output'] = fn

		## svm-train output
		## svm-predict input
		elif fn.endswith(model_params+'.m'):
			files['model'] = fn

		## svm-predict input
		elif fn.endswith('test.txt'):
			files['test'] = fn

		## svm-train input
		elif fn.endswith('train.txt'):
			files['train'] = fn

		## ignore other files
		else:
			continue

	# todo = ['svm-train', 'svm-predict']
	todo = []
	# predicted
	if files['output']:
		# do nothing
		pass

	# trained, to predict
	elif files['output'] == False and files['model']:
		todo = [ (libsvm['test'], files['test']) ]

	# not even trained, to train and then to predict
	elif files['output'] == False and files['model'] == False and (files['train'] and files['test']):
		# todo = 

		todo = [ (libsvm['train'], files['train']), (libsvm['test'], files['test'])]

	# some file are missing
	else:
		print >> sys.stderr, '[error] check files', files
		todo = False

	return todo


def parse_params(str_params):
	# target forms: ["-c 4 -b 1", "-c 4-b1", "-c4 -b1", "c4b1", "c4 b1", "c4 b 1"]
	return sorted( re.findall(r'-?([a-z])\s*([0-9])', str_params), key=lambda x:x[0] )


def exec_svm(todo):
	# print os.getcwd()

	# ./svm-train -c 4 -b 1 tmp/537193e3d4388c33d581668a.train.txt tmp/537193e3d4388c33d581668a.b1c4.m
	# ./svm-predict -b 1 tmp/537193e3d4388c33d581668a.test.txt tmp/537193e3d4388c33d581668a.b1c4.m tmp/537193e3d4388c33d581668a.b1c4.out

	for (program, fn) in todo:
		print color.render(' '.join(['>'*5,'start',program]), 'y') 


		print 'exec program:',program
		program_abs_path = os.path.join(libsvm_path, program)
		# cmd = os.path.join(, exec_path)

		print program_abs_path
		

		print 'input:', fn
		fp = os.path.join(file_root, fn)
		print color.render(' '.join(['<'*5, 'finish',program]), 'g')


		if program == 'svm-train':
			program_args = []

		# retcode = subprocess.call([program_abs_path, program_params] + program_args, shell=False)
		# retcode = subprocess.call(['/Users/Maxis/tools/libsvm-3.17/tools/checkdata.py','tmp/537193e3d4388c33d581668a.test.txt'], shell=False)
		# retcode = subprocess.call('/Users/Maxis/tools/libsvm-3.17/tools/checkdata.py tmp/537193e3d4388c33d581668a.test.txt', shell=True)

	# print '='*100,'\nretcode:',retcode
	# subprocess.call()

if __name__ == '__main__':

	import getopt

	add_opts = [
		('--setting', ['--setting: specify a setting ID (e.g., 537086fcd4388c7e81676914)', 
					   '           which can be retrieved from the mongo collection features.settings' ]),
		('--param', ['--param: parameter string for libsvm (e.g., use "c4b1" or "-c 4 -b 1" to represent the libsvm parameters -c 4 -b 1)'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hvo',['help', 'verbose', 'overwrite', 'setting=', 'param='])
	except getopt.GetoptError:
		config.help('run_svm', addon=add_opts, exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('run_svm', addon=add_opts)
		elif opt in ('--param'): libsvm_params = parse_params( arg.strip() )
		elif opt in ('--setting'): setting_id = arg.strip()
			# setting_id = arg.strip() if len(arg.strip()) > 0 else None
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True

	## files related to this setting id
	# 537193e3d4388c33d581668a.default.m
	# 537193e3d4388c33d581668a.default.out
	# 537193e3d4388c33d581668a.gold.txt
	# 537193e3d4388c33d581668a.test.txt
	# 537193e3d4388c33d581668a.train.txt
	related_files = [x for x in os.listdir(file_root) if x.startswith(setting_id)]

	## model params: looks like "default" or "b1c4"
	## the options string will be in the ascending alphabet order after runing parse_params()
	# print libsvm_params
	model_params = 'default' if len(libsvm_params) == 0 else ''.join( [k+v for k,v in libsvm_params ] )
	
	print 'related_files:',related_files	## ['5371bc38d4388c470a7fb71f.gold.txt', '5371bc38d4388c470a7fb71f.test.txt', '5371bc38d4388c470a7fb71f.train.txt']
	print 'model_params:',model_params		## b1c4

	## check current files
	## use model_params to check "5371bc38d4388c470a7fb71f.b1c4.m" and "5371bc38d4388c470a7fb71f.b1c4.out"
	
	
	## generate workflow

	## execute programs

	# check current status and obtain the to-do-list
	# todo = get_to_do_list(related_files, model_params)
	# print 'todo:',todo


	# exec_svm(todo)
	# pass