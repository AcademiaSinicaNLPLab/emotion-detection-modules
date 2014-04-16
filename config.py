# -*- coding: utf-8 -*-
import sys

mongo_addr = 'doraemon.iis.sinica.edu.tw'
verbose = False

## mongo collection name
co_emotions_name = 'emotions'
co_docs_name = 'docs'
co_pats_name = 'pats'
co_lexicon_name = 'lexicon'

co_patscore_names = ['patscore_0', 'patscore_1', 'patscore_2']
#co_docscore_names = [ ['docscore_0_0', 'docscore_0_1', 'docscore_0_2'], ['docscore_1_0', 'docscore_1_1', 'docscore_1_2'] ]
co_docscore_names = [ ['docscore_0_0', 'docscore_0_1', 'docscore_0_2', 'docscore_0_3'], ['docscore_1_0', 'docscore_1_1', 'docscore_1_2', 'docscore_1_3'] ]

## names of functions
ps_function_name = 'ps_function'
ds_function_name = 'ds_function'
sig_function_name = 'sig_function'
smoothing_name = 'smoothing'

## functions
ps_function_type = 0
smoothing_type = 0

ds_function_type = 0
sig_function_type = 0
# epsilon = 0.5

## utils
def toStr(fields="ps_function,ds_function,sig_function,smoothing", key_value='=', parameters=','):
	fields_to_transform = [x.strip() for x in fields.split(',')]

	cfg = {}

	if 'ps_function' in fields_to_transform:
		cfg[ps_function_name] = ps_function_type

	if 'ds_function' in fields_to_transform:
		cfg[ds_function_name] = ds_function_type

	if 'sig_function' in fields_to_transform:
		cfg[sig_function_name] = sig_function_type

	if 'smoothing' in fields_to_transform:
		cfg[smoothing_name] = smoothing_type

	return parameters.join([ str(x)+key_value+str(cfg[x]) for x in sorted( cfg.keys() ) ])


def help(program, exit=1):

	params = {}

	params['-p'] = [
		'-p, --ps_function: pattern scoring function',
		'                 0: (default) no distribution information, only consider occurrence portion',
		'                 1: combine occurrence with distribution information using standard deviation scaling [2014.03.18]',
		'                 2: average occurrence with weight [2014.04.09]']

	params['-d'] = [
		'-d, --ds_function: document scoring function',
		'                 0: (default) arithmetic mean',
		'                 1: geometric mean']
	params['-g'] = [
		'-g, --sig_function: significance function',
		'                 0: (default) sf = 1, i.e., remain origin pattern score',
		'                 1: sf = ( pattern length )',
		'                 2: sf = ( 1/sentence length )',
		'                 3: sf = ( pattern length/sentence length )']
	params['-s'] = [
		'-s, --smoothing: smoothing method',
		'                 0: (default) no smoothig',
		'                 1: naive smoothing (+1)']

	params['-v'] = [
		'-v, --verbose: show debug message']


	if program == 'document_scoring':
		opts = ['-p','-d','-s','-g','-v']
	elif program == 'pattern_scoring':
		opts = ['-p','-s','-v']

	usage = 'usage: python '+program+'.py [options]\n' + '='*50 + '\n[options]'
	params_str = '\n'.join(['\n'.join(params[opt]) + '\n' for opt in opts])


	print >> sys.stderr, usage
	print >> sys.stderr, params_str

	if exit: sys.exit(exit)

