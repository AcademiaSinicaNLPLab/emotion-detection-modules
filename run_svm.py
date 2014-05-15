
import config
import os, sys, re

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
setting_id = '537193e3d4388c33d581668a'
# setting_id = '537086fcd4388c7e81676914'

libsvm_path = '/Users/Maxis/tools/libsvm-3.17'

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
			files['output'] = True

		## svm-train output
		## svm-predict input
		elif fn.endswith(model_params+'.m'):
			files['model'] = True

		## svm-predict input
		elif fn.endswith('test.txt'):
			files['test'] = True

		## svm-train input
		elif fn.endswith('train.txt'):
			files['train'] = True

		## ignore other files
		else:
			continue

	todo = ['svm-train', 'svm-predict']
	# predicted
	if files['output']:
		todo = []
	# trained, to predict
	elif files['output'] == False and files['model']:
		todo = ['svm-predict']
	# not even trained, to train and then to predict
	elif files['output'] == False and files['model'] == False and (files['train'] and files['test']):
		todo = ['svm-train']
	# some file are missing
	else:
		print >> sys.stderr, '[error] check files', files
		todo = False

	return todo


def parse_params(str_params):
	# target forms: ["-c 4 -b 1", "-c 4-b1", "-c4 -b1", "c4b1", "c4 b1", "c4 b 1"]
	libsvm_params = re.findall(r'-?([a-z])\s*([0-9])', str_params)
	libsvm_params.sort(key=lambda x:x[0])
	return libsvm_params

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
		elif opt in ('--param'): 
			libsvm_params = arg.strip() if len(arg.strip()) > 0 else parse_params
			
		elif opt in ('--setting'): setting_id = arg.strip()
			# setting_id = arg.strip() if len(arg.strip()) > 0 else None
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True



	## files related to this setting id
	related_files = [x for x in os.listdir(file_root) if x.startswith(setting_id)]
	# 537193e3d4388c33d581668a.default.m
	# 537193e3d4388c33d581668a.default.out
	# 537193e3d4388c33d581668a.gold.txt
	# 537193e3d4388c33d581668a.test.txt
	# 537193e3d4388c33d581668a.train.txt

	## model params will look like "default" or "b1c4"
	## (the options are in the ascending alphabet order)
	model_params = 'default' if len(libsvm_params) == 0 else ''.join( [k+v for k,v in libsvm_params ] )
	
	print related_files
	print model_params

	# check current status and obtain the to-do-list
	todo = get_to_do_list(related_files, model_params)
	print todo
	# pass