from typing import List

import numpy as np
import pytest

from scicamera.formats import (
    SensorFormat,
    round_up_to_multiple,
    unpack_csi_padded,
    unpack_raw,
)

_10BIT = SensorFormat("SBGGR10_CSI2P")
_12BIT = SensorFormat("SBGGR12_CSI2P")


def bitstring_to_bytes(s):
    s = s.replace(" ", "")
    s = s.replace("_", "")

    bytez = int(s, 2).to_bytes((len(s) + 7) // 8, byteorder="big")
    padding = round_up_to_multiple(len(bytez), 32) - len(bytez)

    return bytez + (b"\x00" * padding)


def test_unpack_raw_12bit_minimum():
    raw_12_bit = np.zeros(32, dtype=np.uint8)
    unpacked = unpack_raw(raw_12_bit, (1, 2), _12BIT)
    np.testing.assert_array_equal(unpacked, np.zeros((1, 2), dtype=np.uint16))


def test_unpack_raw_10bit_minimum():
    raw_10_bit = np.zeros(32, dtype=np.uint8)
    unpacked = unpack_raw(raw_10_bit, (1, 4), _10BIT)
    np.testing.assert_array_equal(unpacked, np.zeros((1, 4), dtype=np.uint16))
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
    out_shape = (1, 4)
    bytez = bitstring_to_bytes(inp)
    array = np.frombuffer(bytez, dtype=np.uint8)

    unpacked = unpack_raw(array, out_shape, _10BIT)
    assert unpacked.shape == out_shape
    np.testing.assert_array_equal(
        unpacked, np.array(expected, dtype=np.uint16).reshape(out_shape)
    )


zero = "0" * 12
full = "1" * 12


@pytest.mark.parametrize(
    "inp,expected",
    [
        # AAAAAAAA BBBBBBBB AAAA BBBB
        ("00000000 00000000 0000 0000", [0, 0]),
        ("00000000 00000000 0001 0001", [1, 1]),
        ("00000000 00000000 0010 0010", [2, 2]),
        ("00000000 00000000 0100 0100", [4, 4]),
        ("00000000 00000000 1000 1000", [8, 8]),
        ("00000001 00000001 0000 0000", [16, 16]),
        ("00000010 00000010 0000 0000", [32, 32]),
        ("00000100 00000100 0000 0000", [64, 64]),
        ("00001000 00001000 0000 0000", [128, 128]),
        ("00010000 00010000 0000 0000", [256, 256]),
        ("00100000 00100000 0000 0000", [512, 512]),
        ("01000000 01000000 0000 0000", [1024, 1024]),
        ("10000000 10000000 0000 0000", [2048, 2048]),
        ("00000000 00000000 0000 0001", [1, 0]),
        ("00000000 00000000 0000 0011", [3, 0]),
        ("00001111 00000000 0000 1111", [255, 0]),
        ("00010000 00000000 0000 0000", [256, 0]),
        ("00100000 00000000 0000 0000", [512, 0]),
        ("01000000 00000000 0000 0000", [1024, 0]),
        ("10000000 00000000 0000 0000", [2048, 0]),
        ("11111111 00000000 0000 1111", [4095, 0]),
        ("00000000 00000000 0001 0000", [0, 1]),
        ("00000000 00000000 0011 0000", [0, 3]),
        ("00000000 00001111 1111 0000", [0, 255]),
        ("00000000 00010000 0000 0000", [0, 256]),
        ("00000000 00100000 0000 0000", [0, 512]),
        ("00000000 01000000 0000 0000", [0, 1024]),
        ("00000000 10000000 0000 0000", [0, 2048]),
        ("00000000 11111111 1111 0000", [0, 4095]),
        ("10000000 00000000 0001 0001", [2049, 1]),
        ("10000000 00000000 0011 0001", [2049, 3]),
        ("10000000 00001111 1111 0001", [2049, 255]),
        ("10000000 00010000 0000 0001", [2049, 256]),
        ("10000000 00100000 0000 0001", [2049, 512]),
        ("10000000 01000000 0000 0001", [2049, 1024]),
        ("10000000 10000000 0000 0001", [2049, 2048]),
        ("10000000 11111111 1111 0001", [2049, 4095]),
        ("00000000 11111111 1111 0000", [0, 4095]),
        ("11111111 00000000 0000 1111", [4095, 0]),
    ],
)
def test_unpack_raw_12bit(inp: str, expected: List[int]):
    out_shape = (1, len(expected))
    bytez = bitstring_to_bytes(inp)
    array = np.frombuffer(bytez, dtype=np.uint8)
    unpacked = unpack_raw(array, out_shape, _12BIT)
    assert unpacked.shape == out_shape
    np.testing.assert_array_equal(
        unpacked, np.array(expected, dtype=np.uint16).reshape(out_shape)
    )


@pytest.mark.parametrize("size", (1, 2, 10, 1000, 10000))
def test_unpack_sizes_10bit(size: int):
    out_shape = (1, size)
    raw_10_bit = np.zeros(round_up_to_multiple(size * 10 / 8, 32), dtype=np.uint8)
    unpacked = unpack_raw(raw_10_bit, out_shape, _10BIT)
    np.testing.assert_array_equal(unpacked, np.zeros(out_shape, dtype=np.uint16))


@pytest.mark.parametrize("size", (1, 2, 10, 1000, 10000))
def test_unpack_sizes_12bit(size: int):
    out_shape = (1, size)
    raw_12_bit = np.zeros(round_up_to_multiple(size * 12 / 8, 32), dtype=np.uint8)
    unpacked = unpack_raw(raw_12_bit, out_shape, _12BIT)
    assert unpacked.shape == out_shape


def test_unpack_padded_imx477():
    # IMX477 12-bit CSI2P
    fmt = SensorFormat("SBGGR12_CSI2P")
    raw = np.zeros(18580480, dtype=np.uint8)
    nominal_size = (3040, 4056)

    unpacked = unpack_csi_padded(raw, nominal_size, fmt)
    assert unpacked.dtype == np.uint16
    assert unpacked.shape == nominal_size


def test_unpack_padded_imx219():
    # IMX219 10-bit CSI2P
    fmt = SensorFormat("SBGGR10_CSI2P")
    raw = np.zeros(10171392, dtype=np.uint8)
    nominal_size = (2464, 3280)

    unpacked = unpack_csi_padded(raw, nominal_size, fmt)
    assert unpacked.dtype == np.uint16
    assert unpacked.shape == nominal_size
