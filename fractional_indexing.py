"""
Provides functions for generating ordering strings

<https://observablehq.com/@dgreensp/implementing-fractional-indexing>

<https://github.com/httpie/fractional-indexing-python>.

"""
from math import floor
from typing import Optional, List
import decimal


__version__ = '0.1.1'
__licence__ = 'CC0 1.0 Universal'

BASE_62_DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


class FIError(Exception):
    pass


def midpoint(a: str, b: Optional[str], digits: str) -> str:
    """
    `a` may be empty string, `b` is null or non-empty string.
    `a < b` lexicographically if `b` is non-null.
    no trailing zeros allowed.
    digits is a string such as '0123456789' for base 10.  Digits must be in
    ascending character code order!

    """
    zero = digits[0]
    if b is not None and a >= b:
        raise FIError(f'{a} >= {b}')
    if (a and a[-1]) == zero or (b is not None and b[-1] == zero):
        raise FIError('trailing zero')
    if b:
        # remove longest common prefix.  pad `a` with 0s as we
        # go.  note that we don't need to pad `b`, because it can't
        # end before `a` while traversing the common prefix.
        n = 0
        for x, y in zip(a.ljust(len(b), zero), b):
            if x == y:
                n += 1
                continue
            break

        if n > 0:
            return b[:n] + midpoint(a[n:], b[n:], digits)

    # first digits (or lack of digit) are different
    try:
        digit_a = digits.index(a[0]) if a else 0
    except IndexError:
        digit_a = -1
    try:
        digit_b = digits.index(b[0]) if b is not None else len(digits)
    except IndexError:
        digit_b = -1

    if digit_b - digit_a > 1:
        min_digit = round_half_up(0.5 * (digit_a + digit_b))
        return digits[min_digit]
    else:
        if b is not None and len(b) > 1:
            return b[:1]
        else:
            # `b` is null or has length 1 (a single digit).
            # the first digit of `a` is the previous digit to `b`,
            # or 9 if `b` is null.
            # given, for example, midpoint('49', '5'), return
            # '4' + midpoint('9', null), which will become
            # '4' + '9' + midpoint('', null), which is '495'
            return digits[digit_a] + midpoint(a[1:], None, digits)


def validate_integer(i: str):
    if len(i) != get_integer_length(i[0]):
        raise FIError(f'invalid integer part of order key: {i}')


def get_integer_length(head):
    if 'a' <= head <= 'z':
        return ord(head) - ord('a') + 2
    elif 'A' <= head <= 'Z':
        return ord('Z') - ord(head[0]) + 2
    raise FIError('invalid order key head: ' + head)


def get_integer_part(key: str) -> str:
    integer_part_length = get_integer_length(key[0])
    if integer_part_length > len(key):
        raise FIError(f'invalid order key: {key}')
    return key[:integer_part_length]


def validate_order_key(key: str, digits=BASE_62_DIGITS):
    zero = digits[0]
    smallest = 'A' + (zero * 26)
    if key == smallest:
        raise FIError(f'invalid order key: {key}')

    # get_integer_part() will throw if the first character is bad,
    # or the key is too short.  we'd call it to check these things
    # even if we didn't need the result
    i = get_integer_part(key)
    f = key[len(i):]
    if f and f[-1] == zero:
        raise FIError(f'invalid order key: {key}')


def increment_integer(x: str, digits: str) -> Optional[str]:
    zero = digits[0]
    validate_integer(x)
    head, *digs = x
    carry = True
    for i in reversed(range(len(digs))):
        d = digits.index(digs[i]) + 1
        if d == len(digits):
            digs[i] = zero
        else:
            digs[i] = digits[d]
            carry = False
            break
    if carry:
        if head == 'Z':
            return 'a' + zero
        elif head == 'z':
            return None
        h = chr(ord(head[0]) + 1)
        if h > 'a':
            digs.append(zero)
        else:
            digs.pop()
        return h + ''.join(digs)
    else:
        return head + ''.join(digs)


def decrement_integer(x, digits):
    validate_integer(x)
    head, *digs = x
    borrow = True
    for i in reversed(range(len(digs))):

        try:
            index = digits.index(digs[i])
        except IndexError:
            index = -1
        d = index - 1

        if d == -1:
            digs[i] = digits[-1]
        else:
            digs[i] = digits[d]
            borrow = False
            break
    if borrow:
        if head == 'a':
            return 'Z' + digits[-1]
        if head == 'A':
            return None
        h = chr(ord(head[0]) - 1)
        if h < 'Z':
            digs.append(digits[-1])
        else:
            digs.pop()
        return h + ''.join(digs)
    else:
        return head + ''.join(digs)


def generate_key_between(a: Optional[str], b: Optional[str], digits=BASE_62_DIGITS) -> str:
    """
    `a` is an order key or null (START).
    `b` is an order key or null (END).
    `a < b` lexicographically if both are non-null.
    digits is a string such as '0123456789' for base 10.  Digits must be in
    ascending character code order!

    """
    zero = digits[0]
    if a is not None:
        validate_order_key(a, digits=digits)
    if b is not None:
        validate_order_key(b, digits=digits)
    if a is not None and b is not None and a >= b:
        raise FIError(f'{a} >= {b}')

    if a is None:
        if b is None:
            return 'a' + zero
        ib = get_integer_part(b)
        fb = b[len(ib):]
        if ib == 'A' + (zero * 26):
            return ib + midpoint('', fb, digits)
        if ib < b:
            return ib
        res = decrement_integer(ib, digits)
        if res is None:
            raise FIError('cannot decrement any more')
        return res

    if b is None:
        ia = get_integer_part(a)
        fa = a[len(ia):]
        i = increment_integer(ia, digits)
        return ia + midpoint(fa, None, digits) if i is None else i

    ia = get_integer_part(a)
    fa = a[len(ia):]
    ib = get_integer_part(b)
    fb = b[len(ib):]
    if ia == ib:
        return ia + midpoint(fa, fb, digits)
    i = increment_integer(ia, digits)
    if i is None:
        raise FIError('cannot increment any more')

    if i < b:
        return i

    return ia + midpoint(fa, None, digits)


def generate_n_keys_between(a: Optional[str], b: Optional[str], n: int, digits=BASE_62_DIGITS) -> List[str]:
    """
    same preconditions as generate_keys_between().
    n >= 0.
    Returns an array of n distinct keys in sorted order.
    If a and b are both null, returns [a0, a1, ...]
    If one or the other is null, returns consecutive "integer"
    keys.  Otherwise, returns relatively short keys between

    """
    if n == 0:
        return []
    if n == 1:
        return [generate_key_between(a, b, digits)]
    if b is None:
        c = generate_key_between(a, b, digits)
        result = [c]
        for i in range(n - 1):
            c = generate_key_between(c, b, digits)
            result.append(c)
        return result

    if a is None:
        c = generate_key_between(a, b, digits)
        result = [c]
        for i in range(n - 1):
            c = generate_key_between(a, c, digits)
            result.append(c)
        return list(reversed(result))

    mid = floor(n / 2)
    c = generate_key_between(a, b, digits)
    return [
        *generate_n_keys_between(a, c, mid, digits),
        c,
        *generate_n_keys_between(c, b, n - mid - 1, digits)
    ]


def round_half_up(n: float) -> int:
    """
    >>> round_half_up(0.4)
    0
    >>> round_half_up(0.8)
    1
    >>> round_half_up(0.5)
    1
    >>> round_half_up(1.5)
    2
    >>> round_half_up(2.5)
    3
    """
    return int(
        decimal.Decimal(str(n)).quantize(
            decimal.Decimal('1'),
            rounding=decimal.ROUND_HALF_UP
        )
    )
