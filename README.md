# Fractional Indexing

> This library is based on [Implementing Fractional Indexing
](https://observablehq.com/@dgreensp/implementing-fractional-indexing) by [David Greenspan](https://github.com/dgreensp).
> Fractional indexing is a technique to create an ordering that can be used
for [Realtime Editing of Ordered Sequences](https://www.figma.com/blog/realtime-editing-of-ordered-sequences/). 
This implementation includes variable-length integers and the prepend/append optimization described in David's article.


This is a Python port of the original JavaScript implementation from [rocicorp/fractional-indexing](https://github.com/rocicorp/fractional-indexing).
The current version is compatible with v4 of the original ([see changelog](#changelog)).

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
argument to `generate_key_between()`, `generate_n_keys_between()`, and `validate_order_key()`.

Every key starts with a "head" character that encodes the length of its integer part. Since v4.0.0 (matching the
JS reference v4.0.0), the head alphabet (`int_digits`) defaults to `digits` itself, so a custom alphabet produces
self-contained keys drawn only from that alphabet:

```python
from fractional_indexing import generate_key_between


assert generate_key_between(None, None, digits='0123456789') == '50'
assert generate_key_between('50', None, digits='0123456789') == '51'

```

To keep the pre-0.2 behaviour (`A-Z`/`a-z` head markers, e.g. `a0`), pass `BASE_52_DIGITS` as `int_digits`.
An odd-length alphabet such as Base95 cannot supply its own (even-length) head alphabet, so it must be paired
with an explicit `int_digits`:

```python
from fractional_indexing import BASE_52_DIGITS, generate_key_between, generate_n_keys_between, validate_order_key


BASE_95_DIGITS = ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'

assert generate_key_between(None, None, digits=BASE_95_DIGITS, int_digits=BASE_52_DIGITS) == 'a '
assert generate_key_between('a ', None, digits=BASE_95_DIGITS, int_digits=BASE_52_DIGITS) == 'a!'
assert generate_key_between(None, 'a ', digits=BASE_95_DIGITS, int_digits=BASE_52_DIGITS) == 'Z~'

assert generate_n_keys_between('a ', 'a!', n=3, digits=BASE_95_DIGITS, int_digits=BASE_52_DIGITS) == ['a 8', 'a P', 'a h']

validate_order_key('a ', digits=BASE_95_DIGITS, int_digits=BASE_52_DIGITS)

```

Alphabets are validated: they must be at least two characters, single-byte (char code 0-255), and in strictly
ascending character-code order; `int_digits` must also have even length. Invalid alphabets raise `FIError`.

## Other Languages

This is a Python port of the original JavaScript implementation by [@rocicorp](https://github.com/rocicorp)
(as of its v4.0.0). That means that this implementation is byte-for-byte compatible with:

| Language   | Repo                                                                                        |
|------------|---------------------------------------------------------------------------------------------|
| JavaScript | [rocicorp/fractional-indexing](https://github.com/rocicorp/fractional-indexing)             |
| Go         | [rocicorp/fracdex](https://github.com/rocicorp/fracdex)                                     |
| Kotlin     | [darvelo/fractional-indexing-kotlin](https://github.com/darvelo/fractional-indexing-kotlin) |
| Ruby       | [kazu-2020/fractional_indexer](https://github.com/kazu-2020/fractional_indexer)             |

## Changelog

Starting with v4, we mirror the major version number of the original JS implementation to indicate compatibility.

### 4.0.0 (2026-08-06)

Brings the library to parity with [rocicorp/fractional-indexing](https://github.com/rocicorp/fractional-indexing)
v4.0.0:

- **Breaking**: the head alphabet now defaults to `digits` itself, so custom alphabets produce self-contained keys
  (e.g. `generate_key_between(None, None, digits='0123456789')` returns `'50'`, not `'a0'`). Pass
  `int_digits=BASE_52_DIGITS` to restore the previous `A-Z`/`a-z` head markers. Keys generated with the default
  Base62 alphabet are unchanged.
- New `int_digits` argument on `generate_key_between()`, `generate_n_keys_between()`, and `validate_order_key()`
  to customise the head alphabet, plus a new `BASE_52_DIGITS` export.
- `generate_key_between()` now accepts its bounds in either order and swaps them, instead of raising `FIError`.
- Alphabets are validated (length, ascending character-code order, single-byte); invalid alphabets and unknown
  digits now raise `FIError` consistently instead of leaking `ValueError`.
- Digit lookups are cached per alphabet, and the midpoint calculation uses integer arithmetic (the `decimal`
  dependency is gone).

### 0.1.2 (2023-08-03)

Bug fixes.

### 0.1.0 (2022-02-02)

Initial release.
