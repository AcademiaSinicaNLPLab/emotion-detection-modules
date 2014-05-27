## sync tmp folder

import sys
import subprocess
import logging

server = 'doraemon'

progress = False


cmd = ['rsync', '-ar', '--ignore-existing']

if progress:
	cmd.append('--progress')

target_folder = '~/projects/emotion-detection-modules/tmp'

def pull():
	# server -> local
	src = server+':'+target_folder
	dest = target_folder
	print 'pull data from '+server
	# subprocess.call(' '.join(cmd+[src, dest]), shell=True)

def push():
	# local -> server
	src = target_folder
	dest = server+':'+target_folder
	print 'push data to '+server
	print ' '.join(cmd+[src, dest])
	# subprocess.call(' '.join(cmd+[src, dest]), shell=True)

if __name__ == '__main__':
	pull()
	push()