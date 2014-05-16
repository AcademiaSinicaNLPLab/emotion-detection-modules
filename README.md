## [Feelit](http://doraemon.iis.sinica.edu.tw/feelit/)

A key focus of this work was to recognize implicit emotions in blog posts.

Different from past approaches using surface features, we utilize syntax and semantic knowledges and learn meaningful patterns to detect a user's intended emotion.

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
				- position feature [(position_feature.py)](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/position_feature.py)
``` javascript
[options]
-b: percentage of beginning section
-m: percentage of middle section
-e: percentage of ending section
-c: counting unit for document segmentation
                 0: number of words
                 1: number of sentences (not implemented yet)
-f: feature value computation
                 0: pattern scores (patscore_p2_s0)  
                 1: accumulated threshold by 0.68 (1 std) using pattern scores  
                 2: accumulated threshold by 0.68 (1 std) using pattern count  
                 3: type 2 + ignore those with total occurrence < 4 (1, 2, 3)  
                 4: type 2 + remove the pattern occurrence counted from oneself (for ldocID 0-799)  
                 5: type 3 + remove the pattern occurrence counted from oneself (for ldocID 0-799)  
-v, --verbose: show debug message
```

				- pattern feature [(pattern_feature.py)](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/pattern_feature.py)
				
``` javascript
[options]
-l, --limit: minimum occurrence of a pattern
              	  0: (default) collect all patterns
                  n: at least occurs < n > times for each pattern
-v, --verbose: show debug message
```

				- keyword feature [(keyword_feature.py)](https://github.com/AcademiaSinicaNLPLab/emotion-detection-modules/blob/master/keyword_feature.py)
``` javascript
[options]
-k: keyword set in WordNetAffect
                 0: basic
                 1: extend
--lemma: use word lemma when looking for keywords
-v, --verbose: show debug message
```

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
