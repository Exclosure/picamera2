from typing import List

import numpy as np
import pytest

from scicamera.formats import unpack_raw


def bitstring_to_bytes(s):
    s = s.replace(" ", "")
    s = s.replace("_", "")

    return int(s, 2).to_bytes((len(s) + 7) // 8, byteorder="big")


def test_unpack_raw_12bit_minimum():
    raw_10_bit = np.zeros(3, dtype=np.uint8)
    unpacked = unpack_raw(raw_10_bit, "SBGGR12_CSI2P")
    assert unpacked.size == 2


def test_unpack_raw_10bit_minimum():
    raw_10_bit = np.zeros(5, dtype=np.uint8)
    unpacked = unpack_raw(raw_10_bit, "SBGGR10_CSI2P")
    np.testing.assert_array_equal(unpacked, np.zeros(4, dtype=np.uint16))
    assert unpacked.size == 4


zero = "0" * 10
full = "1" * 10


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("00000_00001 00000_00000 00000_00000 00000_00000", [1, 0, 0, 0]),
        ("00000_00011 00000_00000 00000_00000 00000_00000", [3, 0, 0, 0]),
        ("00111_11111 00000_00000 00000_00000 00000_00000", [255, 0, 0, 0]),
        ("01000_00000 00000_00000 00000_00000 00000_00000", [256, 0, 0, 0]),
        ("10000_00000 00000_00000 00000_00000 00000_00000", [512, 0, 0, 0]),
        ("11111_11111 00000_00000 00000_00000 00000_00000", [1023, 0, 0, 0]),
        ("_".join((zero, zero, zero, zero)), [0, 0, 0, 0]),
        ("_".join((full, full, full, full)), [1023, 1023, 1023, 1023]),
        ("_".join((zero, full, full, full)), [0, 1023, 1023, 1023]),
        ("_".join((full, zero, zero, zero)), [1023, 0, 0, 0]),
        ("_".join((zero, zero, zero, full)), [0, 0, 0, 1023]),
        ("_".join((zero, full, zero, full)), [0, 1023, 0, 1023]),
    ],
)
def test_unpack_raw_10bit(inp: str, expected: List[int]):
    bytez = bitstring_to_bytes(inp)
    array = np.frombuffer(bytez, dtype=np.uint8)
    unpacked = unpack_raw(array, "SBGGR10_CSI2P")
    np.testing.assert_array_equal(unpacked, np.array(expected, dtype=np.uint16))


zero = "0" * 12
full = "1" * 12


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("000000_000001 000000_000000", [1, 0]),
        ("000000_000011 000000_000000", [3, 0]),
        ("000011_111111 000000_000000", [255, 0]),
        ("000100_000000 000000_000000", [256, 0]),
        ("001000_000000 000000_000000", [512, 0]),
        ("010000_000000 000000_000000", [1024, 0]),
        ("100000_000000 000000_000000", [2048, 0]),
        ("111111_111111 000000_000000", [4095, 0]),
        ("_".join((zero, zero, zero, zero)), [0, 0, 0, 0]),
        ("_".join((full, full, full, full)), [4095, 4095, 4095, 4095]),
        ("_".join((zero, full, full, full)), [0, 4095, 4095, 4095]),
        ("_".join((full, zero, zero, zero)), [4095, 0, 0, 0]),
        ("_".join((zero, zero, zero, full)), [0, 0, 0, 4095]),
        ("_".join((zero, full, zero, full)), [0, 4095, 0, 4095]),
    ],
)
def test_unpack_raw_12bit(inp: str, expected: List[int]):
    bytez = bitstring_to_bytes(inp)
    array = np.frombuffer(bytez, dtype=np.uint8)
    unpacked = unpack_raw(array, "SBGGR12_CSI2P")
    np.testing.assert_array_equal(unpacked, np.array(expected, dtype=np.uint16))


@pytest.mark.parametrize("size", (1, 2, 10, 1000, 10000))
def test_unpack_sizes_10bit(size: int):
    raw_10_bit = np.zeros(size * 5, dtype=np.uint8)
    unpacked = unpack_raw(raw_10_bit, "SBGGR10_CSI2P")
    assert unpacked.size == size * 4


@pytest.mark.parametrize("size", (1, 2, 10, 1000, 10000))
def test_unpack_sizes_12bit(size: int):
    raw_12_bit = np.zeros(size * 3, dtype=np.uint8)
    unpacked = unpack_raw(raw_12_bit, "SBGGR12_CSI2P")
    assert unpacked.size == size * 2
