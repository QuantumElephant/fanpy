""" Tests for slater_det.py
"""

from slater_det import remove_orbs, add_orbs, excite, is_occupied
from slater_det import remove_pairs, add_pairs, excite_pairs

def test_remove_orbs():
    """ Test remove_orbs function
    """
    # Remove orbs that are not occupied
    assert remove_orbs(0b00110, 0) == 0
    assert remove_orbs(0b00110, 3) == 0
    assert remove_orbs(0b00110, 4) == 0
    assert remove_orbs(0b00110, 5) == 0
    assert remove_orbs(0b00110, 6) == 0
    # Remove orbs that are occupied
    assert remove_orbs(0b00110, 1) == 0b100
    assert remove_orbs(0b00110, 2) == 0b010
    # Remove multiple orbitals
    assert remove_orbs(0b01110, 1, 2) == 0b1000
    assert remove_orbs(0b01110, 2, 1) == 0b1000
    # Remove orb multiple times
    assert remove_orbs(0b00110, 2, 2) == 0
    assert remove_orbs(0b00110, 1, 1) == 0
    # Large index
    n = 9999999
    assert remove_orbs(0b1 | 1 << n, n) == 0b1

def test_add_orbs():
    """ Test add_orbs function
    """
    # Add orbs that are not occupied
    assert add_orbs(0b00110, 0) == 0b111
    assert add_orbs(0b00110, 3) == 0b1110
    assert add_orbs(0b00110, 4) == 0b10110
    assert add_orbs(0b00110, 5) == 0b100110
    assert add_orbs(0b00110, 6) == 0b1000110
    # Add orbs that are occupied
    assert add_orbs(0b00110, 1) == 0
    assert add_orbs(0b00110, 2) == 0
    # Add multiple orbitals
    assert add_orbs(0b01000, 1, 2) == 0b1110
    assert add_orbs(0b01000, 2, 1) == 0b1110
    # Add orb multiple times
    assert add_orbs(0b01100, 1, 1) == 0
    assert add_orbs(0b01010, 2, 2) == 0
    assert add_orbs(0b01100, 1, 1, 1) == 0
    assert add_orbs(0b01010, 2, 2, 2) == 0
    # Large index
    n = 9999999
    assert add_orbs(0b1, n) == 0b1 | 1 << n

def test_excite():
    """ Test excite function
    """
    # Excite from occupied to virtual
    assert excite(0b0001, 0, 1) == 0b10
    assert excite(0b0001, 0, 5) == 0b100000
    assert excite(0b1000, 3, 0) == 0b1
    # Excite from virtual to virtual
    assert excite(0b00100, 0, 1) == 0
    assert excite(0b00100, 9999, 1) == 0
    # Excite from occupied to occupied
    assert excite(0b1001, 3, 0) == 0
    # Large index
    assert excite(0b1001, 3, 999999) == 0b0001 | 1 << 999999

def test_remove_pairs():
    """ Test remove_pairs function
    """
    # Remove pairs that are not occupied
    assert remove_pairs(0b001100, 0) == 0
    assert remove_pairs(0b001100, 2) == 0
    assert remove_pairs(0b001100, 3) == 0
    # Remove pairs that are partially occupied
    assert remove_pairs(0b001010, 0) == 0
    assert remove_pairs(0b000101, 0) == 0
    # Remove pairs that are occupied
    assert remove_pairs(0b001111, 1) == 0b11
    # Remove multiple pairs
    assert remove_pairs(0b11111, 0, 1) == 0b10000
    assert remove_pairs(0b11111, 1, 0) == 0b10000
    # Remove pairs multiple times
    assert remove_pairs(0b001111, 1, 1) == 0
    assert remove_pairs(0b001111, 1, 1, 1) == 0
    # Large index
    n = 999999
    assert remove_pairs(0b1 | 0b11 << n*2, n) == 0b1

def test_add_pairs():
    """ Test add_pairs function
    """
    # Add pairs that are not occupied
    assert add_pairs(0b001100, 0) == 0b1111
    assert add_pairs(0b001100, 2) == 0b111100
    assert add_pairs(0b001100, 3) == 0b11001100
    assert add_pairs(0b001100, 4) == 0b1100001100
    # Add pairs that are occupied
    assert add_pairs(0b001100, 1) == 0
    # Add pairs that are partially occupied
    assert add_pairs(0b001001, 0) == 0
    assert add_pairs(0b001001, 1) == 0
    # Add multiple pairs
    assert add_pairs(0b01100, 0, 2) == 0b111111
    assert add_pairs(0b01100, 2, 0) == 0b111111
    # Add pairs multiple times
    assert add_pairs(0b00011, 0, 0) == 0
    assert add_pairs(0b00011, 1, 1) == 0
    assert add_pairs(0b00011, 0, 0, 0) == 0
    assert add_pairs(0b00011, 1, 1, 1) == 0
    # Large index
    n = 9999999
    assert add_pairs(0b1, n) == 0b1 | 0b11 << n*2

def test_excite_pairs():
    """ Test excite_pairs function
    """
    # Excite_Pairs from occupied to virtual
    assert excite_pairs(0b0011, 0, 1) == 0b1100
    assert excite_pairs(0b0011, 0, 2) == 0b110000
    assert excite_pairs(0b110000, 2, 0) == 0b11
    # Excite_Pairs from virtual to virtual
    assert excite_pairs(0b00100, 0, 2) == 0
    assert excite_pairs(0b00100, 9999, 1) == 0
    # Excite_Pairs from occupied to occupied
    assert excite_pairs(0b110011, 2, 0) == 0
    # Excite pairs from partially occupied
    assert excite_pairs(0b100011, 2, 1) == 0
    assert excite_pairs(0b100011, 2, 0) == 0
    assert excite_pairs(0b100011, 2, 3) == 0
    # Large index
    assert excite_pairs(0b0111, 0, 999999) == 0b100 | 0b11 << 999999*2

def test_is_occupied():
    """ Test is_occupied function
    """
    # Test occupancy
    assert is_occupied(0b100100, 2)
    assert is_occupied(0b100100, 5)
    assert not is_occupied(0b100100, 4)
    assert not is_occupied(0b100100, 6)
    assert not is_occupied(0b100100, 0)
