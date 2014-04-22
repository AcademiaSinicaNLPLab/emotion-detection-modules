
## A blog post from "sleepy"

---
Home sweet home ...

Back in michigan ...

Just in time for winter , but oh well , at least `it 's not` too `bad` out yet

Almost December and it has only snowed twice :-) nice new apartment ...

With a fitness center so i can start toning up now that `i` 've `dropped` damn near 50 lbs -) yay !!!!

hmmmm ...

`things are` pretty `good` . .

engaged since last christmas , :-) do n't have a date set yet , but probably sometime this summer ...

seriously talking about `having` a `baby` ...

but that will happen when it 's meant to

all in `all` things `are` pretty `good`

not complaining too much ... ;-) anywho

`time` to go home and `go to bed`

more massive piles of laundry to do tomorrow

---


## Extracted patterns

pattern  			| cheerful 	| sleepy 	| drained
-------- 			| -------- 	| ------ 	| -------
it is not bad 	|	0.60  		| 	0.7 	|  0.64
i dropped			|	0.76		|	0		|  0.46
things are good 	|	0.64  		|   0.3  	|  0.64
having baby		|	0			|	0		|  0.58
all are good 		|	1.0  		|   0  	|  0
time go to bed	|	0			|	`0.58`	|  0


## Results

1.`cheerful`: 0.35

2.`drained`: 0.32

...

10.`sleepy`: 0.24


## Issues

(__pattern scoring__) 系統可以抓出 salien pattern：`time go to bed` 在 sleepy 的分數相對其他情緒較高！

(__document scoring__) 但卻會被文章中其他 pattern 影響：e.g., `it is not bad`, `i dropped` and `things are good`


## Goal

讓 `重要` pattern 分數更為突出

	
