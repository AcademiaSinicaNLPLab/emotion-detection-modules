emotion-detection-modules
=========================

This repository contains source codes and dev notes of the project "[Feelit](http://doraemon.iis.sinica.edu.tw/feelit/)" at Academia Sinica

## Workflow

1. Extract Patterns from LJ40K
	- program: [extract_pattern.py](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/extract_pattern.py)
	- extract patterns from sentences using dependency relations

2. Construct Lexicon
	- program: [lexicon_construction.py](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/lexicon_construction.py)
	- store emotion, pattern in __mongodb__
	
3. Pattern Scoring
	- program: [pattern_scoring.py](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/pattern_scoring.py)
	- calculate emotion scores for each pattern

4. Document Scoring
	1. naive approache
		- program: [document_scoring.py](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/document_scoring.py)
		- average the emotion scores in each pattern

	2. machine learning
		- program: (comming soon)
		- include
			1. feature extraction
				- position feature [(document_feature.py)](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/document_feature.py)
				- keyword feature
				- pattern feature
			2. training
			3. testing

5. Evaluation
	1. naive document scoring
		- program: [evaluation.py](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/evaluation.py)

	2. machine learning
		- program: [evaluation_svm.py](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/evaluation_svm.py)


## useful git commands

``` 
git clone git@github.com:AcademiaSinicaNLPLab/emotion-detection-modules.git
```

```javascript
// check (un)tracked, (un)staged files
git st

// add files for this commit
git add <files>
git ci -m "add a new line blah..."

// push commit to remote
git push -u origin master	// first time using push
git push

// if cannot push to remote (fast forward), pull first
git pull -u origin master	// first time using pull
git pull
```
