import numpy as np

from scicamera.formats import unpack_raw


def bitstring_to_bytes(s):
    chars = list(c for c in s)
    bytez = b""
    while chars:
        counter = 0
        val = 0
        while counter < 8:
            c = chars.pop(0)
            if c in "_ ":
                continue

            if c == "1":
                val += 2**counter
            counter += 1
        bytez += bytes([val])
    return bytez


def test_unpack_raw_12bit_minimum():
    raw_10_bit = np.zeros(3, dtype=np.uint8)
    unpacked = unpack_raw(raw_10_bit, "SBGGR12_CSI2P")
    assert unpacked.size == 2


def test_unpack_raw_10bit_minimum():
    raw_10_bit = np.zeros(5, dtype=np.uint8)
    unpacked = unpack_raw(raw_10_bit, "SBGGR12_CSI2P")
    assert unpacked.size == 4


def test_unpack_raw_10bit_alignment():
    # bytez = bitstring_to_bytes("1"*10 + "0" * 10 + "1" * 10 + "0" * 10)
    # assert len(bytez) == 5
    # array = np.frombuffer(bytez, dtype=np.uint8)
    # assert array.size == 5

    # unpacked = unpack_raw(array, "SBGGR10_CSI2P")
    # assert np.testing.assert_array_equal(unpacked, np.array([2**16-1, 0, 2**16-1, 0], dtype=np.uint16))
    # assert unpacked.size == 4

    bytez = bitstring_to_bytes("10000_00000 00000_00000 00000_00000 00000_00000")
    assert len(bytez) == 5
    array = np.frombuffer(bytez, dtype=np.uint8)
    assert array.size == 5

    unpacked = unpack_raw(array, "SBGGR10_CSI2P")
    assert np.testing.assert_array_equal(
        unpacked, np.array([2**16 - 1, 0, 2**16 - 1, 0], dtype=np.uint16)
    )
    assert unpacked.size == 4
