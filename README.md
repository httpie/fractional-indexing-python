# Fractional Indexing

This is based on [Implementing Fractional Indexing
](https://observablehq.com/@dgreensp/implementing-fractional-indexing) by [David Greenspan
](https://github.com/dgreensp).

Fractional indexing is a technique to create an ordering that can be used
for [Realtime Editing of Ordered Sequences](https://www.figma.com/blog/realtime-editing-of-ordered-sequences/).

This implementation includes variable-length integers, and the prepend/append optimization described in David's article.

## Installation

```bash
$ pip install fractional-indexing
```

## Usage

### Generate a single key

```python
from fractional_indexing import generate_key_between


# Insert at the beginning
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

# Insert in between 2nd and 3rd (midpoint)
second_and_half = generate_key_between(second, third)
assert second_and_half == 'a1V'

```

### Generate multiple keys

Use this when generating multiple keys at some known position, as it spaces out indexes more evenly and leads to shorter keys.

```python
from fractional_indexing import generate_n_keys_between


# Insert 3 at the beginning
keys = generate_n_keys_between(None, None, n=3)
assert keys == ['a0', 'a1', 'a2']

# Insert 3 after 1st
keys = generate_n_keys_between('a0', None, n=3)
assert keys == ['a1', 'a2', 'a3']

# Insert 3 before 1st
keys = generate_n_keys_between(None, 'a0', n=3)
assert keys == ['Zx', 'Zy', 'Zz']

# Insert 3 in between 2nd and 3rd (midpoint)
keys = generate_n_keys_between('a1', 'a2', n=3)
assert keys == ['a1G', 'a1V', 'a1l']

```

### Validate a key

```python
from fractional_indexing import validate_order_key, FIError


validate_order_key('a0')

try:
    validate_order_key('foo')
except FIError as e:
    print(e)  # fractional_indexing.FIError: invalid order key: foo

```

### Use custom base digits

By default, this library uses Base62 character encoding. To use a different set of digits, pass them in as the `digits`
argument to `generate_key_between()`, `generate_n_keys_between()`, and `validate_order_key()`:

```python
from fractional_indexing import generate_key_between, generate_n_keys_between, validate_order_key


BASE_95_DIGITS = ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'

assert generate_key_between(None, None, digits=BASE_95_DIGITS) == 'a '
assert generate_key_between('a ', None, digits=BASE_95_DIGITS) == 'a!'
assert generate_key_between(None, 'a ', digits=BASE_95_DIGITS) == 'Z~'

assert generate_n_keys_between('a ', 'a!', n=3, digits=BASE_95_DIGITS) == ['a"', 'a#', 'a$']

validate_order_key('a ', digits=BASE_95_DIGITS)

```

## Other Languages

This is a Python port of the original JavaScript implementation by [@rocicorp](https://github.com/rocicorp). That means
that this implementation is byte-for-byte compatible with:

| Language   | Repo                                                  |
|------------|-------------------------------------------------------|
| JavaScript | https://github.com/rocicorp/fractional-indexing       |
| Go         | https://github.com/rocicorp/fracdex                   |
| Kotlin     | https://github.com/darvelo/fractional-indexing-kotlin |
