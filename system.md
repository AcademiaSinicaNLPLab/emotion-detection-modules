system logs
---

```python
python pattern_scoring.py -p 1 -s 0 -v

Time total: 34222.3969491 sec  ## issused caused by ensureIndexes() ??
```


```python
python document_scoring.py -p 0 -d 0 -s 0 -g 0 -v

Cache hit: 6292880
Cache miss: 11082280
Cache hit rate: 0.362176808732
Time total: 2067.79474998 sec
```

```python
python document_scoring.py -p 0 -d 0 -s 0 -g 1 -v

Cache hit: 6292880
Cache miss: 11082280
Cache hit rate: 0.362176808732
Time total: 11901.2810538 sec
```



