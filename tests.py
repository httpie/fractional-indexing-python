from typing import Optional

import pytest

from fractional_indexing import (
    BASE_52_DIGITS,
    BASE_62_DIGITS,
    FIError,
    generate_key_between,
    generate_n_keys_between,
    validate_order_key,
)


BASE_10_DIGITS = '0123456789'
BASE_95_DIGITS = ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'


def check_key(expected, a, b, digits=None, int_digits=None):
    if isinstance(expected, FIError):
        with pytest.raises(FIError) as e:
            generate_key_between(a, b, digits, int_digits)
        assert e.value.args[0] == expected.args[0]
    else:
        assert generate_key_between(a, b, digits, int_digits) == expected


def check_n_keys(expected, a, b, n, digits=None, int_digits=None):
    if isinstance(expected, FIError):
        with pytest.raises(FIError) as e:
            generate_n_keys_between(a, b, n, digits, int_digits)
        assert e.value.args[0] == expected.args[0]
    else:
        assert ' '.join(generate_n_keys_between(a, b, n, digits, int_digits)) == expected


# With no `digits` and no `int_digits` the default is unchanged: BASE_62 digits
# with the A-Z/a-z head markers, so keys still look like 'a0', 'Zz', ...
@pytest.mark.parametrize(['a', 'b', 'expected'], [
    (None, None, 'a0'),
    (None, 'a0', 'Zz'),
    (None, 'Zz', 'Zy'),
    ('a0', None, 'a1'),
    ('a1', None, 'a2'),
    ('a0', 'a1', 'a0V'),
    ('a1', 'a2', 'a1V'),
    ('a0V', 'a1', 'a0l'),
    ('Zz', 'a0', 'ZzV'),
    ('Zz', 'a1', 'a0'),
    (None, 'Y00', 'Xzzz'),
    ('bzz', None, 'c000'),
    ('a0', 'a0V', 'a0G'),
    ('a0', 'a0G', 'a08'),
    ('b125', 'b129', 'b127'),
    ('a0', 'a1V', 'a1'),
    ('Zz', 'a01', 'a0'),
    (None, 'a0V', 'a0'),
    (None, 'b999', 'b99'),
    (None, 'A00000000000000000000000000', FIError('invalid order key: A00000000000000000000000000')),
    (None, 'A000000000000000000000000001', 'A000000000000000000000000000V'),
    ('zzzzzzzzzzzzzzzzzzzzzzzzzzy', None, 'zzzzzzzzzzzzzzzzzzzzzzzzzzz'),
    ('zzzzzzzzzzzzzzzzzzzzzzzzzzz', None, 'zzzzzzzzzzzzzzzzzzzzzzzzzzzV'),
    ('a00', None, FIError('invalid order key: a00')),
    ('a00', 'a1', FIError('invalid order key: a00')),
    ('0', '1', FIError('invalid order key head: 0')),
    # bounds may be passed in either order; they are swapped as a convenience
    ('a1', 'a0', 'a0V'),
])
def test_generate_key_between(a: Optional[str], b: Optional[str], expected) -> None:
    check_key(expected, a, b)


# A custom `digits` with no `int_digits` uses `digits` itself as the head
# alphabet, so base-10 keys contain no letters: heads 0-4 are negative lengths,
# 5-9 positive, and 4/5 mark the shortest (length-2) integer parts.
@pytest.mark.parametrize(['a', 'b', 'n', 'expected'], [
    (None, None, 5, '50 51 52 53 54'),
    ('54', None, 10, '55 56 57 58 59 600 601 602 603 604'),
    (None, '50', 5, '45 46 47 48 49'),
    ('50', '52', 20, '501 502 503 5035 504 505 506 507 508 509 51 511 512 513 514 515 516 517 518 519'),
])
def test_generate_n_keys_between_base_10(a: Optional[str], b: Optional[str], n: int, expected: str) -> None:
    check_n_keys(expected, a, b, n, BASE_10_DIGITS)


# base-95 is odd-length, so it can't supply its own (even) head alphabet;
# pass the default A-Z/a-z markers explicitly to keep Latin heads.
@pytest.mark.parametrize(['a', 'b', 'expected'], [
    ('a00', 'a01', 'a00P'),
    ('a0/', 'a00', 'a0/P'),
    (None, None, 'a '),
    ('a ', None, 'a!'),
    (None, 'a ', 'Z~'),
    ('a0 ', 'a0!', FIError('invalid order key: a0 ')),
    (None, 'A                          0', 'A                          ('),
    ('a~', None, 'b  '),
    ('Z~', None, 'a '),
    ('b   ', None, FIError('invalid order key: b   ')),
    ('a0', 'a0V', 'a0;'),
    ('a  1', 'a  2', 'a  1P'),
    (None, 'A                          ', FIError('invalid order key: A                          ')),
])
def test_base95_digits(a: Optional[str], b: Optional[str], expected) -> None:
    check_key(expected, a, b, BASE_95_DIGITS, BASE_52_DIGITS)


# Custom alphabets that do not contain the Latin head characters a-z/A-Z work
# fine, as long as the digits are even-length, single-byte (char code 0-255),
# and sorted in ascending character-code order. With no `int_digits` the digit
# alphabet itself supplies the integer heads, so the generated keys are
# self-headed (no Latin letters).
@pytest.mark.parametrize(['digits', 'a', 'b', 'n', 'expected'], [
    # Base 2: the integer range is tiny (only heads '0' and '1').
    ('01', None, None, 8, '10 11 111 1111 11111 111111 1111111 11111111'),
    ('01', '10', None, 1, '11'),
    ('01', '10', '11', 1, '101'),
    # Keys must be single-byte: a multi-byte alphabet (e.g. Greek, U+0391..) is
    # rejected, but Latin-1 characters (char code 128-255) are allowed.
    ('ΑΒΓΔΕΖΗΘ', None, None, 10, FIError('digits must be single-byte (char code 0-255): ΑΒΓΔΕΖΗΘ')),
    # A Latin-1 alphabet (¡=161 .. ¦=166), all within the single-byte range.
    ('¡¢£¤¥¦', None, None, 6, '¤¡ ¤¢ ¤£ ¤¤ ¤¥ ¤¦'),
    # An alphabet of symbols whose character codes are all below 'A'.
    (' !#$%&', None, None, 6, '$  $! $# $$ $% $&'),
])
def test_custom_alphabets(digits: str, a: Optional[str], b: Optional[str], n: int, expected) -> None:
    check_n_keys(expected, a, b, n, digits)


# `int_digits` overrides the integer-part head alphabet (which defaults to the
# digit alphabet, or to the A-Z/a-z markers when no `digits` is given).  It is a
# single ascending (lexicographically ordered) alphabet: the first half are the
# negative-length heads and the second half the positive-length heads.
# Restricting it to a shorter alphabet limits how long the integer part may
# grow, and any head outside `int_digits` is invalid.
@pytest.mark.parametrize(['digits', 'int_digits', 'a', 'b', 'expected'], [
    # Limit negative heads to 'A','B' and positive heads to 'a','b'; the inner
    # pair (B, a) mark length 2 and the outer pair (A, b) mark length 3.
    (BASE_10_DIGITS, 'ABab', 'a0', 'a1', 'a05'),
    (BASE_10_DIGITS, 'ABab', 'a9', None, 'b00'),
    (BASE_10_DIGITS, 'ABab', 'b00', None, 'b01'),
    (BASE_10_DIGITS, 'ABab', 'a0', None, 'a1'),
    (BASE_10_DIGITS, 'ABab', None, 'B9', 'B8'),
    # A head outside the limited alphabet is rejected.
    (BASE_10_DIGITS, 'ABab', 'c00', None, FIError('invalid order key head: c')),
    (BASE_10_DIGITS, 'ABab', '00', '01', FIError('invalid order key head: 0')),
    # `int_digits` may be identical to `digits` (which is also the default),
    # producing keys with no letters at all: the first half (0-4) are negative
    # heads and the second half (5-9) positive heads, so 4 and 5 mark the
    # shortest (length-2) integer parts.
    (BASE_10_DIGITS, BASE_10_DIGITS, None, None, '50'),
    (BASE_10_DIGITS, BASE_10_DIGITS, '50', None, '51'),
    (BASE_10_DIGITS, BASE_10_DIGITS, '59', None, '600'),
    (BASE_10_DIGITS, BASE_10_DIGITS, None, '50', '49'),
    (BASE_10_DIGITS, BASE_10_DIGITS, '56', '57', '565'),
])
def test_int_digits(digits: str, int_digits: str, a: Optional[str], b: Optional[str], expected) -> None:
    check_key(expected, a, b, digits, int_digits)


# `digits` and `int_digits` are validated once at the start of the public API.
# `digits` must be at least two characters in strictly ascending character-code
# order (which also rules out duplicates).  `int_digits` must additionally be of
# even length (its two halves are the negative- and positive-length heads).
@pytest.mark.parametrize(['digits', 'int_digits', 'expected'], [
    ('0213456789', 'ABab',
     FIError('digits must be at least 2 characters in strictly ascending character code order: 0213456789')),
    ('0', 'ABab',
     FIError('digits must be at least 2 characters in strictly ascending character code order: 0')),
    ('0012', 'ABab',
     FIError('digits must be at least 2 characters in strictly ascending character code order: 0012')),
    (BASE_10_DIGITS, 'abc',
     FIError('int_digits must be an even number of at least 2 characters in strictly ascending character code order: abc')),
    (BASE_10_DIGITS, 'ba',
     FIError('int_digits must be an even number of at least 2 characters in strictly ascending character code order: ba')),
    (BASE_10_DIGITS, '',
     FIError('int_digits must be an even number of at least 2 characters in strictly ascending character code order: ')),
    (BASE_10_DIGITS, 'ΑΒΓΔ',
     FIError('int_digits must be single-byte (char code 0-255): ΑΒΓΔ')),
    # An odd-length `digits` with no explicit `int_digits` cannot supply its own
    # (even-length) head alphabet.  (The reference JS implementation skips this
    # check and silently produces broken keys; we raise instead.)
    (BASE_95_DIGITS, None,
     FIError('int_digits must be an even number of at least 2 characters in strictly '
             f'ascending character code order: {BASE_95_DIGITS}')),
])
def test_alphabet_validation(digits: str, int_digits: Optional[str], expected: FIError) -> None:
    check_key(expected, None, None, digits, int_digits)
    check_n_keys(expected, None, None, 5, digits, int_digits)


class LCG:
    """Deterministic pseudo-random generator so test runs are reproducible."""

    def __init__(self, seed: int = 1) -> None:
        self.seed = seed

    def random(self) -> float:
        self.seed = (self.seed * 1103515245 + 12345) & 0x7FFFFFFF
        return self.seed / 0x7FFFFFFF


# Generated keys must sort with ordinary lexicographic comparison for any
# ascending alphabet.  Insert at random positions and verify ordering holds.
@pytest.mark.parametrize(['digits', 'int_digits'], [
    (BASE_10_DIGITS, None),
    (' !#$%&', None),
    ('¡¢£¤¥¦', None),
    (BASE_62_DIGITS, None),
    # base 2 self-heading has too small an integer range to sustain 1000
    # inserts, so give it the wider A-Z/a-z head alphabet.
    ('01', BASE_52_DIGITS),
    # digits and int_digits identical (base-10 keys with no letters).
    (BASE_10_DIGITS, BASE_10_DIGITS),
    # the all-defaults classic form.
    (None, None),
])
def test_ordering(digits: Optional[str], int_digits: Optional[str]) -> None:
    rnd = LCG()
    keys = []
    for _ in range(1000):
        pos = int(rnd.random() * (len(keys) + 1))
        a = keys[pos - 1] if pos > 0 else None
        b = keys[pos] if pos < len(keys) else None
        k = generate_key_between(a, b, digits, int_digits)
        assert (a is None or a < k) and (b is None or k < b), f'out of range: {a} < {k} < {b}'
        keys.insert(pos, k)
    assert keys == sorted(keys)


def test_omitted_int_digits_matches_digits() -> None:
    # An omitted `int_digits` defaults to `digits`, so it must behave
    # identically to passing `digits` as the head alphabet.
    rnd = LCG()
    keys = []
    for _ in range(2000):
        pos = int(rnd.random() * (len(keys) + 1))
        a = keys[pos - 1] if pos > 0 else None
        b = keys[pos] if pos < len(keys) else None
        default = generate_key_between(a, b, BASE_10_DIGITS)
        explicit = generate_key_between(a, b, BASE_10_DIGITS, BASE_10_DIGITS)
        assert default == explicit
        keys.insert(pos, default)


def test_equal_bounds_rejected() -> None:
    with pytest.raises(FIError):
        generate_key_between('a0', 'a0')


def test_readme_examples_single_key():
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

    # Insert in between 2nd and 3rd. Midpoint
    second_and_half = generate_key_between(second, third)
    assert second_and_half == 'a1V'


def test_readme_examples_multiple_keys():
    # Insert 3 at the beginning
    keys = generate_n_keys_between(None, None, n=3)
    assert keys == ['a0', 'a1', 'a2']

    # Insert 3 after 1st
    keys = generate_n_keys_between('a0', None, n=3)
    assert keys == ['a1', 'a2', 'a3']

    # Insert 3 before 1st
    keys = generate_n_keys_between(None, 'a0', n=3)
    assert keys == ['Zx', 'Zy', 'Zz']

    # Insert 3 in between 2nd and 3rd. Midpoint
    keys = generate_n_keys_between('a1', 'a2', n=3)
    assert keys == ['a1G', 'a1V', 'a1l']


def test_readme_examples_validate_order_key():
    validate_order_key('a0')

    with pytest.raises(FIError) as e:
        validate_order_key('foo')
    assert e.value.args[0] == 'invalid order key: foo'


def test_readme_examples_custom_base():
    validate_order_key('a ', digits=BASE_95_DIGITS, int_digits=BASE_52_DIGITS)
    kwargs = {'digits': BASE_95_DIGITS, 'int_digits': BASE_52_DIGITS}
    assert generate_key_between(None, None, **kwargs) == 'a '
    assert generate_key_between('a ', None, **kwargs) == 'a!'
    assert generate_key_between(None, 'a ', **kwargs) == 'Z~'
    assert generate_n_keys_between('a ', 'a!', n=3, **kwargs) == ['a 8', 'a P', 'a h']
