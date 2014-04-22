## A blog post from "sleepy"

```c
Home sweet home ...
Back in michigan ...
Just in time for winter , but oh well , at least "it is not" too "bad" out yet
Almost December and it has only snowed twice :-) nice new apartment ...
With a fitness center so i can start toning up now that "i" have "dropped" damn near 50 lbs -) yay !!!!
hmmmm ...
"things are" pretty "good" . .
engaged since last christmas , :-) do not have a date set yet , but probably sometime this summer ...
seriously talking about "having" a "baby" ...
but that will happen when it is meant to
all in "all" things "are" pretty "good"
not complaining too much ... ;-) anywho
"time" to go home and "go to bed"
more massive piles of laundry to do tomorrow
```

## Extracted patterns

pattern  		| cheerful 	| sleepy 	| drained
-------- 		| -------- 	| ------ 	| -------
it is not bad 		|	0.55  	| 	0.68 	|  0.60
i dropped		|	0.66	|	0	|  0.38
things are good 	|	0.56  	|	0.24  	|  0.56
having baby		|	0	|	0	|  0.5
all are good 		|	1.0  	|	0  	|  0
**time go to bed**	|	0	|	0.5	|  0


## Results

rank	| emotion 	| score 
-------	| ------	| ----
1	| cheerful	| 0.088
2	| drained	| 0.072
3	| hungry	| 0.067
4	| **sleepy**	| 0.059
5	| exhausted	| 0.057
..	| ...		| ...



## Issues

這篇是來自 sleepy 的文章

(__pattern scoring__) 系統可以抓出 salien pattern：`time go to bed` 在 sleepy 的分數相對其他情緒較高！

(__document scoring__) 但卻會被文章中其他 pattern 影響：e.g., `it is not bad`, `i dropped` and `things are good`

最後使得 sleepy 落在第四名


## Goal

讓 **重要** pattern 分數更為突出

	
