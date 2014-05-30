import os, subprocess

if __name__ == '__main__':

	sid = sys.argv[1].strip()
	param = sys.argv[2].strip()

	subprocess.call(['python', 'run_binary_svm.py', sid, param], shell=False)
	subprocess.call(['python', 'evaluate_binary.py', sid, param], shell=False)
	
	