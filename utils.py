# fractional_indexing/utils.py

import decimal
from typing import Optional

from exceptions import OrderKeyError

BASE_62_DIGITS: str = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def round_half_up(value: float) -> int:
    """Round a float to the nearest integer, rounding halves up."""
    return int(
        decimal.Decimal(str(value)).quantize(
            decimal.Decimal('1'),
            rounding=decimal.ROUND_HALF_UP
        )
    )


def validate_integer(order_key: str) -> None:
    """Validate that the length of the integer part of the order key is correct."""
    if len(order_key) != get_integer_length(order_key[0]):
        raise OrderKeyError(f'Invalid integer part of order key: {order_key}')


def get_integer_length(first_char: str) -> int:
    """Return the length of the integer part based on the first character."""
    if 'a' <= first_char <= 'z':
        return ord(first_char) - ord('a') + 2
    elif 'A' <= first_char <= 'Z':
        return ord('Z') - ord(first_char) + 2
    raise OrderKeyError('Invalid order key head: ' + first_char)


def get_integer_part(order_key: str) -> str:
    """Extract the integer part of the order key."""
    integer_part_length = get_integer_length(order_key[0])
    if integer_part_length > len(order_key):
        raise OrderKeyError(f'Invalid order key: {order_key}')
    return order_key[:integer_part_length]


def validate_order_key(order_key: str, digits: str = BASE_62_DIGITS) -> None:
    """Check the validity of an order key."""
    zero = digits[0]
    smallest_valid_key = 'A' + (zero * 26)

    if order_key == smallest_valid_key:
        raise OrderKeyError(f'Invalid order key: {order_key}')

    integer_part = get_integer_part(order_key)
    fractional_part = order_key[len(integer_part):]

    if fractional_part and fractional_part[-1] == zero:
        raise OrderKeyError(f'Invalid order key: {order_key}')


def find_middle_key(start_key: str, end_key: Optional[str], digits: str) -> str:
    """
    Calculate the midpoint between two order keys.
    `start_key` must be lexicographically less than `end_key`.
    No trailing zeros allowed in the order key.
    """
    zero = digits[0]

    if end_key is not None and start_key >= end_key:
        raise OrderKeyError(f'{start_key} >= {end_key}')

    if (start_key and start_key[-1] == zero) or (end_key and end_key[-1] == zero):
        raise OrderKeyError('Trailing zero in order key')

    if end_key:
        common_prefix_len = 0
        for char_start, char_end in zip(start_key.ljust(len(end_key), zero), end_key):
            if char_start == char_end:
                common_prefix_len += 1
                continue
            break

        if common_prefix_len > 0:
            return end_key[:common_prefix_len] + find_middle_key(
                start_key[common_prefix_len:], end_key[common_prefix_len:], digits
            )

    # Different first digits or lack of digit
    digit_a = digits.index(start_key[0]) if start_key else 0
    digit_b = digits.index(end_key[0]) if end_key else len(digits)

    if digit_b - digit_a > 1:
        min_digit = round_half_up(0.5 * (digit_a + digit_b))
        return digits[min_digit]

    if end_key and len(end_key) > 1:
        return end_key[:1]

    return digits[digit_a] + find_middle_key(start_key[1:], None, digits)


def increment_integer(integer_str: str, digits: str) -> Optional[str]:
    """Increment the integer part of the order key."""
    zero = digits[0]
    validate_integer(integer_str)

    head, *digits_list = integer_str
    has_carry_over = True

    for i in reversed(range(len(digits_list))):
        current_digit = digits.index(digits_list[i]) + 1
        if current_digit == len(digits):
            digits_list[i] = zero
        else:
            digits_list[i] = digits[current_digit]
            has_carry_over = False
            break

    if has_carry_over:
        if head == 'Z':
            return 'a' + zero
        if head == 'z':
            return None
        next_head = chr(ord(head) + 1)
        if next_head > 'a':
            digits_list.append(zero)
        else:
            digits_list.pop()
        return next_head + ''.join(digits_list)

    return head + ''.join(digits_list)


def decrement_integer(integer_str: str, digits: str) -> Optional[str]:
    """Decrement the integer part of the order key."""
    validate_integer(integer_str)

    head, *digits_list = integer_str
    requires_borrow = True

    for i in reversed(range(len(digits_list))):
        current_digit = digits.index(digits_list[i]) - 1

        if current_digit == -1:
            digits_list[i] = digits[-1]
        else:
            digits_list[i] = digits[current_digit]
            requires_borrow = False
            break

    if requires_borrow:
        if head == 'a':
            return 'Z' + digits[-1]
        if head == 'A':
            return None
        next_head = chr(ord(head) - 1)
        if next_head < 'Z':
            digits_list.append(digits[-1])
        else:
            digits_list.pop()
        return next_head + ''.join(digits_list)

    return head + ''.join(digits_list)
