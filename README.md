# Fractional Indexing


This is based on [Implementing Fractional Indexing
](https://observablehq.com/@dgreensp/implementing-fractional-indexing) by [David Greenspan
](https://github.com/dgreensp).

Fractional indexing is a technique to create an ordering that can be used for [Realtime Editing of Ordered Sequences](https://www.figma.com/blog/realtime-editing-of-ordered-sequences/).

This implementation includes variable-length integers, and the prepend/append optimization described in David's article.

## Installation

```bash
$ pip install fractional-indexing
```


## Usage

```python
from fractional_indexing import generate_key_between


first = generate_key_between(None, None)
assert first == 'a0'

# Insert after 1st
second = generate_key_between(first, None)
assert second == 'a1'

# Insert after 2nd
third = generate_key_between(second, None)
assert third == 'a2'

# Insert before 1st
zeroth = generate_key_between(None, first)
assert zeroth == 'Zz'

# Insert in between 2nd and 3rd. Midpoint
second_and_half = generate_key_between(second, third)
assert second_and_half == 'a1V'

```

## Other Languages

This is a Python port of the original JavaScript implementation by [@rocicorp](https://github.com/rocicorp). That means that this implementation is byte-for-byte compatible with:

| Language   | Repo                                                 |
| ---------- | ---------------------------------------------------- |
| JavaScript | https://github.com/rocicorp/fractional-indexing      |
| Go         | https://github.com/rocicorp/fracdex                  |
