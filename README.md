# java-decorator-search
Find stuff based on decorators

# Setup

```
$ python3 -m venv
# pip install javalang
```

# Usage

```
$ ./src/java-decorator-search.py /path/to/folder --ignore TestCases
...
>>> # Find functions where *any* decorator matches
>>> ds.findAny(lambda d: d.name == 'Path').pretty()

>>> # Find functions where *all* decorators match (useful for negative searches)
>>> ds.findAll(lambda d: d.name != 'SecurityCheck').pretty()

>>> # Chain searches together
>>> ds.findAll(lambda d: d.name != 'SecurityCheck').findAny(lambda d: d.value == 'Super').pretty()

```
