import pytest
from twopidgeons.utils import is_valid_filename, calculate_hash

def test_is_valid_filename():
    assert is_valid_filename("abcde.2pg") is True
    assert is_valid_filename("fghij.2pg") is True
    
    # Invalid cases
    assert is_valid_filename("abc.2pg") is False # Too short
    assert is_valid_filename("abcdef.2pg") is False # Too long
    assert is_valid_filename("ABCDE.2pg") is False # Uppercase
    assert is_valid_filename("abcde.jpg") is False # Wrong extension
    assert is_valid_filename("12345.2pg") is False # Numbers
    assert is_valid_filename(".2pg") is False # No name

def test_calculate_hash():
    data = b"test data"
    # SHA256 of "test data"
    expected_hash = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert calculate_hash(data) == expected_hash
