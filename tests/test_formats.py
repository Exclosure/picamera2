from typing import List

import numpy as np
import pytest

from scicamera.formats import (
    SensorFormat,
    debayer_bilinear,
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


def test_debayer_bilinear():
    # all red pixels are 2, all green pixels are 5, all blue pixels are 3
    # fmt: off
    mosaic = np.array([[2, 5,   2, 5,   2, 5,   2, 5],
                       [5, 3,   5, 3,   5, 3,   5, 3],

                       [2, 5,   2, 5,   2, 5,   2, 5],
                       [5, 3,   5, 3,   5, 3,   5, 3],

                       [2, 5,   2, 5,   2, 5,   2, 5],
                       [5, 3,   5, 3,   5, 3,   5, 3],
    ])
    # fmt: on

    rgb = debayer_bilinear(mosaic)
    assert rgb.shape == mosaic.shape + (3,)

    trimmed = rgb[1:-1, 1:-1, :]

    print(rgb[:, :, 0])
    print(rgb[:, :, 1])
    print(rgb[:, :, 2])

    np.testing.assert_array_equal(trimmed[:, :, 0], 2)
    np.testing.assert_array_equal(trimmed[:, :, 1], 5)
    np.testing.assert_array_equal(trimmed[:, :, 2], 3)
