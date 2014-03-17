emotion-detection-modules
=========================

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


---

* #####[pattern.md](pattern.md)

	pattern extraction modules and database structures
	
* #####[pattern.new.md](pattern.new.md)

	new system architecture (03/13)

* #####[scoring.md](scoring.md)

	scoring functions

####/data

* `LJ2M.emolist`

	128 emotion classes in LJ2M

* `LJ40K.emolist`

	40 emotion classes in LJ40K

* `Mishne05.emolist</code>

	37 emotion classes used by Mishen 2005

* `WordNetAffectKeywords.json`

	1,050 emotion keywords acquired from WordNet Affect

* `WordNetAffectKeywordsExt.json`

	3,785 emotion keywords extended from WordNet Affect using synonyms

