"""
Provides functions for generating ordering strings

<https://github.com/httpie/fractional-indexing-python>

Python port of:
<https://github.com/rocicorp/fractional-indexing> (v4.0.0)

Which is based on:
<https://observablehq.com/@dgreensp/implementing-fractional-indexing>


"""
from __future__ import annotations

from functools import lru_cache
from math import floor
from typing import List, Optional


__version__ = '4.0.0'
__licence__ = 'CC0 1.0 Universal'

__all__ = [
    'BASE_62_DIGITS',
    'BASE_52_DIGITS',
    'FIError',
    'generate_key_between',
    'generate_n_keys_between',
    'validate_order_key',
]

BASE_62_DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

# The classic head-marker alphabet (A-Z + a-z), used as the default `int_digits`
# when `digits` is omitted. Pass it explicitly to keep the pre-0.2 "a0"-style
# heads with a custom digit alphabet.
BASE_52_DIGITS = BASE_62_DIGITS[10:]


class FIError(Exception):
    pass


@lru_cache(maxsize=None)
def _digit_index(digits: str) -> dict:
    """
    Per-alphabet map of each digit to its index, so digit->value lookups are a
    single dict access instead of O(alphabet) ``str.index`` calls. Lookups use
    ``.get(char, 0)``, mirroring the reference JS implementation's Uint8Array
    table which returns 0 for characters outside the alphabet.
    """
    return {c: i for i, c in enumerate(digits)}


def _is_strictly_ascending(s: str) -> bool:
    """
    True if every character has a strictly greater character code than the one
    before it (ascending order, which also rules out duplicates).
    """
    return all(ord(s[i - 1]) < ord(s[i]) for i in range(1, len(s)))


def _is_single_byte(s: str) -> bool:
    """
    True if every character is single-byte (code point 0-255). Keys are required
    to be single-byte so that they stay compatible with the reference JS
    implementation, whose lookup tables only cover char codes 0-255.
    """
    return all(ord(c) <= 255 for c in s)


@lru_cache(maxsize=None)
def _validate_digits(digits: str) -> None:
    """
    Validates a fractional-digit alphabet: at least two characters, in strictly
    ascending character-code order. Cached per alphabet: validation is pure and
    its result never changes, so each alphabet is only scanned once.
    (``lru_cache`` does not cache raised exceptions, only the success path.)
    """
    if len(digits) < 2 or not _is_strictly_ascending(digits):
        raise FIError(
            f'digits must be at least 2 characters in strictly ascending character code order: {digits}'
        )
    if not _is_single_byte(digits):
        raise FIError(f'digits must be single-byte (char code 0-255): {digits}')


@lru_cache(maxsize=None)
def _validate_int_digits(int_digits: str) -> None:
    """
    Validates a head-marker alphabet: an even number of at least two characters
    (its two halves are the negative- and positive-length heads), in strictly
    ascending character-code order.
    """
    if len(int_digits) < 2 or len(int_digits) % 2 != 0 or not _is_strictly_ascending(int_digits):
        raise FIError(
            'int_digits must be an even number of at least 2 characters in strictly '
            f'ascending character code order: {int_digits}'
        )
    if not _is_single_byte(int_digits):
        raise FIError(f'int_digits must be single-byte (char code 0-255): {int_digits}')


def _resolve_alphabets(digits: Optional[str], int_digits: Optional[str]) -> tuple:
    """
    Applies the default resolution shared by every public entry point:
    `int_digits` defaults to `digits`, and when `digits` is also omitted it
    falls back to BASE_52_DIGITS (A-Z/a-z) so the default keys keep the classic
    "a0", "Zz", ... form. `digits` itself defaults to BASE_62_DIGITS.

    Both alphabets are always validated, including a defaulted `int_digits`
    (the reference JS implementation skips that check and silently produces
    broken keys for an odd-length `digits`; we raise instead).
    """
    int_digits_defaulted = int_digits is None
    if int_digits is not None:
        _validate_int_digits(int_digits)
    else:
        int_digits = digits if digits is not None else BASE_52_DIGITS
    if digits is not None:
        _validate_digits(digits)
    else:
        digits = BASE_62_DIGITS
    if int_digits_defaulted:
        _validate_int_digits(int_digits)
    return digits, int_digits


def _midpoint(a: str, b: Optional[str], digits: str, lookup: dict) -> str:
    """
    `a` may be empty string, `b` is null or non-empty string.
    `a < b` lexicographically if `b` is non-null.
    no trailing zeros allowed.

    """
    zero = digits[0]
    if b is not None and a >= b:
        raise FIError(f'{a} >= {b}')
    if (a and a[-1] == zero) or (b is not None and b[-1] == zero):
        raise FIError('trailing zero')
    if b:
        # remove longest common prefix.  pad `a` with 0s as we
        # go.  note that we don't need to pad `b`, because it can't
        # end before `a` while traversing the common prefix.
        n = 0
        while n < len(b) and (a[n] if n < len(a) else zero) == b[n]:
            n += 1
        if n > 0:
            return b[:n] + _midpoint(a[n:], b[n:], digits, lookup)

    # first digits (or lack of digit) are different
    digit_a = lookup.get(a[0], 0) if a else 0
    digit_b = lookup.get(b[0], 0) if b is not None else len(digits)
    if digit_b - digit_a > 1:
        # round half up, matching JS Math.round()
        mid_digit = (digit_a + digit_b + 1) // 2
        return digits[mid_digit]
    else:
        # first digits are consecutive
        if b is not None and len(b) > 1:
            return b[:1]
        else:
            # `b` is null or has length 1 (a single digit).
            # the first digit of `a` is the previous digit to `b`,
            # or 9 if `b` is null.
            # given, for example, midpoint('49', '5'), return
            # '4' + midpoint('9', null), which will become
            # '4' + '9' + midpoint('', null), which is '495'
            return digits[digit_a] + _midpoint(a[1:], None, digits, lookup)


def _validate_integer(i: str, int_digits: str, int_lookup: dict) -> None:
    if len(i) != _get_integer_length(i[0], int_digits, int_lookup):
        raise FIError(f'invalid integer part of order key: {i}')


def _get_integer_length(head: str, int_digits: str, int_lookup: dict) -> int:
    """
    `int_digits` is a single lexicographically ordered (ascending) alphabet: the
    first half are the negative-length heads and the second half the
    positive-length heads (the default A-Z/a-z markers are just one such
    alphabet). The outermost characters mark the longest integer parts, and the
    two heads straddling the midpoint mark the shortest (length 2).
    """
    i = int_lookup.get(head, 0)
    # `.get` returns 0 for characters outside the alphabet, so confirm the
    # character really is at index `i` before trusting it as a head.
    if int_digits[i] == head:
        half = len(int_digits) // 2
        return half - i + 1 if i < half else i - half + 2
    raise FIError(f'invalid order key head: {head}')


def _get_integer_part(key: str, int_digits: str, int_lookup: dict) -> str:
    integer_part_length = _get_integer_length(key[0], int_digits, int_lookup)
    if integer_part_length > len(key):
        raise FIError(f'invalid order key: {key}')
    return key[:integer_part_length]


@lru_cache(maxsize=None)
def _smallest_integer(digits: str, int_digits: str) -> str:
    """
    The smallest integer is the most-negative head (the first character of
    `int_digits`, marking the longest integer part) followed by all-zero digits.
    """
    return int_digits[0] + digits[0] * (len(int_digits) // 2)


def _validate_order_key(key: str, digits: str, int_digits: str, int_lookup: dict) -> None:
    if key == _smallest_integer(digits, int_digits):
        raise FIError(f'invalid order key: {key}')
    # _get_integer_part() will throw if the first character is bad,
    # or the key is too short.  we'd call it to check these things
    # even if we didn't need the result
    i = _get_integer_part(key, int_digits, int_lookup)
    f = key[len(i):]
    if f and f[-1] == digits[0]:
        raise FIError(f'invalid order key: {key}')


def _increment_integer(
    x: str, digits: str, lookup: dict, int_digits: str, int_lookup: dict,
) -> Optional[str]:
    """
    note that this may return None, as there is a largest integer

    """
    _validate_integer(x, int_digits, int_lookup)
    head = x[0]
    zero = digits[0]
    # Walk the digit run right-to-left, turning maxed-out digits into zeros
    # (`trailing`) until we find one we can bump.
    trailing = ''
    for i in range(len(x) - 1, 0, -1):
        d = lookup.get(x[i], 0) + 1
        if d == len(digits):
            trailing = zero + trailing
        else:
            return x[:i] + digits[d] + trailing
    # carry out of the whole digit run; `trailing` is now all zeros.
    head_index = int_lookup.get(head, 0)
    if head_index == len(int_digits) - 1:
        # already the largest integer
        return None
    h = int_digits[head_index + 1]
    # the head moves one step toward the largest digit; grow or shrink the digit
    # run to match the new head's integer length.
    length_delta = (
        _get_integer_length(h, int_digits, int_lookup)
        - _get_integer_length(head, int_digits, int_lookup)
    )
    if length_delta > 0:
        return h + trailing + zero
    if length_delta < 0:
        return h + trailing[1:]
    return h + trailing


def _decrement_integer(
    x: str, digits: str, lookup: dict, int_digits: str, int_lookup: dict,
) -> Optional[str]:
    """
    note that this may return None, as there is a smallest integer

    """
    _validate_integer(x, int_digits, int_lookup)
    head = x[0]
    last = digits[-1]
    # Walk the digit run right-to-left, turning underflowed digits into the
    # largest digit (`trailing`) until we find one we can drop.
    trailing = ''
    for i in range(len(x) - 1, 0, -1):
        d = lookup.get(x[i], 0) - 1
        if d == -1:
            trailing = last + trailing
        else:
            return x[:i] + digits[d] + trailing
    # borrow out of the whole digit run; `trailing` is now all max digits.
    head_index = int_lookup.get(head, 0)
    if head_index == 0:
        # already the smallest integer
        return None
    h = int_digits[head_index - 1]
    # the head moves one step toward the smallest digit; grow or shrink the
    # digit run to match the new head's integer length.
    length_delta = (
        _get_integer_length(h, int_digits, int_lookup)
        - _get_integer_length(head, int_digits, int_lookup)
    )
    if length_delta > 0:
        return h + trailing + last
    if length_delta < 0:
        return h + trailing[1:]
    return h + trailing


def validate_order_key(key: str, digits: Optional[str] = None, int_digits: Optional[str] = None) -> None:
    """
    Validates that `key` is a well-formed order key for the given alphabets.
    Raises FIError if it is not. Alphabet defaults are resolved the same way as
    in `generate_key_between()`.
    """
    digits, int_digits = _resolve_alphabets(digits, int_digits)
    _validate_order_key(key, digits, int_digits, _digit_index(int_digits))


def generate_key_between(
    a: Optional[str],
    b: Optional[str],
    digits: Optional[str] = None,
    int_digits: Optional[str] = None,
) -> str:
    """
    Generates an order key that sorts between `a` and `b`.

    `a` is the lower bound: an order key, or None for the start.
    `b` is the upper bound: an order key, or None for the end.
    When both are non-None, they may be passed in either order.

    `digits` is the alphabet, e.g. '0123456789' for base 10. Its characters
    must be single-byte (char code 0-255) and in ascending character code
    order; both are validated. It may otherwise be any alphabet (it does not
    need to contain 0-9, A-Z or a-z). Because `int_digits` defaults to
    `digits`, an odd-length `digits` must be paired with an explicit
    even-length `int_digits`.

    Note that `digits` only defines the *digit values* of a key. The integer
    part of every key also begins with a length/magnitude marker (a "head")
    drawn from the `int_digits` alphabet. The head only ever occupies the first
    position and is only compared against other heads, which is why `digits`
    and `int_digits` may overlap (or be identical) and keys still sort
    correctly.

    `int_digits` is the head alphabet: a single alphabet in ascending
    (lexicographical) character order, with even length. Its first half are the
    negative-length heads and its second half the positive-length heads. The
    outermost characters mark the longest integer parts and the two characters
    straddling the midpoint mark the shortest (length 2). The integer part may
    grow until it reaches the outermost heads, so a shorter alphabet limits how
    large/small a key's integer part can become.

    `int_digits` defaults to `digits`, so a base-10 alphabet produces
    self-headed keys like "50", "600" or "49". When `digits` is also omitted it
    falls back to BASE_52_DIGITS (A-Z/a-z), giving the classic "a0", "b00",
    "Z9" form. Note that passing `digits` explicitly (even BASE_62_DIGITS)
    makes the keys self-headed; only omitting `digits` entirely yields the
    A-Z/a-z heads.

    >>> generate_key_between(None, None)
    'a0'
    >>> generate_key_between(None, None, '0123456789')
    '50'

    """
    digits, int_digits = _resolve_alphabets(digits, int_digits)
    lookup = _digit_index(digits)
    int_lookup = _digit_index(int_digits)
    if a is not None:
        _validate_order_key(a, digits, int_digits, int_lookup)
    if b is not None:
        _validate_order_key(b, digits, int_digits, int_lookup)
    if a is not None and b is not None and a > b:
        # swap if out of order, so that a < b.  this is just a convenience for
        # callers, and doesn't affect the properties of the generated key.
        a, b = b, a

    if a is None:
        if b is None:
            # the shortest positive head: the first character of the second
            # half of int_digits ("a" for the default A-Z/a-z markers).
            head = int_digits[len(int_digits) // 2]
            return head + digits[0]
        ib = _get_integer_part(b, int_digits, int_lookup)
        fb = b[len(ib):]
        if ib == _smallest_integer(digits, int_digits):
            return ib + _midpoint('', fb, digits, lookup)
        if ib < b:
            return ib
        res = _decrement_integer(ib, digits, lookup, int_digits, int_lookup)
        if res is None:
            raise FIError('cannot decrement any more')
        return res

    if b is None:
        ia = _get_integer_part(a, int_digits, int_lookup)
        fa = a[len(ia):]
        i = _increment_integer(ia, digits, lookup, int_digits, int_lookup)
        return ia + _midpoint(fa, None, digits, lookup) if i is None else i

    ia = _get_integer_part(a, int_digits, int_lookup)
    fa = a[len(ia):]
    ib = _get_integer_part(b, int_digits, int_lookup)
    fb = b[len(ib):]
    if ia == ib:
        return ia + _midpoint(fa, fb, digits, lookup)
    i = _increment_integer(ia, digits, lookup, int_digits, int_lookup)
    if i is None:
        raise FIError('cannot increment any more')
    if i < b:
        return i
    return ia + _midpoint(fa, None, digits, lookup)


def generate_n_keys_between(
    a: Optional[str],
    b: Optional[str],
    n: int,
    digits: Optional[str] = None,
    int_digits: Optional[str] = None,
) -> List[str]:
    """
    same preconditions as generate_key_between().
    n must be >= 0 (raises FIError otherwise).
    Returns an array of n distinct keys in sorted order.
    If a and b are both null, returns [a0, a1, ...]
    If one or the other is null, returns consecutive "integer"
    keys.  Otherwise, returns relatively short keys between `a` and `b`.

    """
    digits, int_digits = _resolve_alphabets(digits, int_digits)
    if n < 0:
        # Without this guard a negative n silently returns a single key when
        # one bound is None, and recurses without bound when both are set.
        raise FIError(f'n must be >= 0: {n}')
    if n == 0:
        return []
    if n == 1:
        return [generate_key_between(a, b, digits, int_digits)]
    if b is None:
        c = generate_key_between(a, b, digits, int_digits)
        result = [c]
        for _ in range(n - 1):
            c = generate_key_between(c, b, digits, int_digits)
            result.append(c)
        return result

    if a is None:
        c = generate_key_between(a, b, digits, int_digits)
        result = [c]
        for _ in range(n - 1):
            c = generate_key_between(a, c, digits, int_digits)
            result.append(c)
        return list(reversed(result))

    mid = floor(n / 2)
    c = generate_key_between(a, b, digits, int_digits)
    return [
        *generate_n_keys_between(a, c, mid, digits, int_digits),
        c,
        *generate_n_keys_between(c, b, n - mid - 1, digits, int_digits),
    ]
