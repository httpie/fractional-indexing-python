from typing import Optional

import pytest

from fractional_indexing import FIError, generate_key_between, generate_n_keys_between, validate_order_key


BASE_95_DIGITS = ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'


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
    ('a1', 'a0', FIError('a1 >= a0')),
])
def test_generate_key_between(a: Optional[str], b: Optional[str], expected: str) -> None:
    if isinstance(expected, FIError):
        with pytest.raises(FIError) as e:
            generate_key_between(a, b)
        assert e.value.args[0] == expected.args[0]
    else:
        act = generate_key_between(a, b)
        print(f'exp: {expected}')
        print(f'act: {act}')
        print(act == expected)
        assert act == expected


@pytest.mark.parametrize(['a', 'b', 'n', 'expected'], [
    (None, None, 5, 'a0 a1 a2 a3 a4'),
    ('a4', None, 10, 'a5 a6 a7 a8 a9 b00 b01 b02 b03 b04'),
    (None, 'a0', 5, 'Z5 Z6 Z7 Z8 Z9'),
    ('a0', 'a2', 20, 'a01 a02 a03 a035 a04 a05 a06 a07 a08 a09 a1 a11 a12 a13 a14 a15 a16 a17 a18 a19'),
])
def test_generate_n_keys_between(a: Optional[str], b: Optional[str], n: int, expected: str) -> None:
    base_10_digits = '0123456789'
    act = ' '.join(generate_n_keys_between(a, b, n, base_10_digits))
    print()
    print(f'exp: {expected}')
    print(f'act: {act}')
    print(act == expected)
    assert act == expected


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
def test_base95_digits(a: Optional[str], b: Optional[str], expected: str) -> None:
    kwargs = {
        'a': a,
        'b': b,
        'digits': BASE_95_DIGITS,
    }
    if isinstance(expected, FIError):
        with pytest.raises(FIError) as e:
            generate_key_between(**kwargs)
        assert e.value.args[0] == expected.args[0]
    else:
        act = generate_key_between(**kwargs)
        print()
        print(f'exp: {expected}')
        print(f'act: {act}')
        print(act == expected)
        assert act == expected


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
    from fractional_indexing import validate_order_key, FIError

    validate_order_key('a0')

    try:
        validate_order_key('foo')
    except FIError as e:
        print(e)  # fractional_indexing.FIError: invalid order key: foo


def test_readme_examples_custom_base():
    validate_order_key('a ', digits=BASE_95_DIGITS)
    assert generate_key_between(None, None, digits=BASE_95_DIGITS) == 'a '
    assert generate_key_between('a ', None, digits=BASE_95_DIGITS) == 'a!'
    assert generate_key_between(None, 'a ', digits=BASE_95_DIGITS) == 'Z~'
    assert generate_n_keys_between('a ', 'a!', n=3, digits=BASE_95_DIGITS) == ['a 8', 'a P', 'a h']
