# -*- coding: utf-8 -*-

mongo_addr = 'doraemon.iis.sinica.edu.tw'

## mongo collection name
co_emotions_name = 'emotions'
co_lexicon_name = 'lexicon'
co_patscore_name = 'patscore'

## names of functions
ps_function_name = 'ps_function'
ds_function_name = 'ds_function'
sig_function_name = 'sig_function'
smoothing_name = 'smoothing'

## functions
ps_function_type = 0
smoothing_type = 0

ds_function_type = 1
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
