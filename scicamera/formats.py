from __future__ import annotations
import math
from typing import Tuple, Literal
from scipy.ndimage import convolve

import numpy as np
from scicamera.sensor_format import SensorFormat

YUV_FORMATS = {"NV21", "NV12", "YUV420", "YVU420", "YVYU", "YUYV", "UYVY", "VYUY"}

RGB_FORMATS = {"BGR888", "RGB888", "XBGR8888", "XRGB8888"}

BAYER_FORMATS = {
    "SBGGR8",
    "SGBRG8",
    "SGRBG8",
    "SRGGB8",
    "SBGGR10",
    "SGBRG10",
    "SGRBG10",
    "SRGGB10",
    "SBGGR10_CSI2P",
    "SGBRG10_CSI2P",
    "SGRBG10_CSI2P",
    "SRGGB10_CSI2P",
    "SBGGR12",
    "SGBRG12",
    "SGRBG12",
    "SRGGB12",
    "SBGGR12_CSI2P",
    "SGBRG12_CSI2P",
    "SGRBG12_CSI2P",
    "SRGGB12_CSI2P",
}

MONO_FORMATS = {"R8", "R10", "R12", "R8_CSI2P", "R10_CSI2P", "R12_CSI2P"}

ALL_FORMATS = YUV_FORMATS | RGB_FORMATS | BAYER_FORMATS | MONO_FORMATS


def is_YUV(fmt: str) -> bool:
    return fmt in YUV_FORMATS


def is_RGB(fmt: str) -> bool:
    return fmt in RGB_FORMATS


def is_Bayer(fmt: str) -> bool:
    return fmt in BAYER_FORMATS


def is_mono(fmt: str) -> bool:
    return fmt in MONO_FORMATS


def is_raw(fmt: str) -> bool:
    return is_Bayer(fmt) or is_mono(fmt)


def is_format_valid(fmt: str) -> bool:
    return fmt in ALL_FORMATS


def assert_format_valid(fmt: str) -> None:
    if not is_format_valid(fmt):
        raise ValueError(f"Invalid format: {fmt}. Valid formats are: {ALL_FORMATS}")


def _assert_is_byte_array(array: np.ndarray) -> None:
    assert array.dtype == np.uint8, "Raw unpack only accepts uint8 arrays"
    assert array.ndim == 1, "Unpack raw only accepts flat arrays"


# NOTE(meawoppl) - the below implementations are a bit memory inefficient when it comes
# to deserialization of the 10/12 bit arrays, as it will overallocated by 1/5 and 1/3
# respectively. This is a tradeoff for simplicity of implementation using numpy.
# The approach breaks down to the following:
# - Compute the number of bytes needed at which the data realigns itself to the next byte boundary
#   - for 10 bit (4 pixels) - 40 bits, 5 bytes
#   - fot 12 bit (2 pixels) - 24 bits, 3 bytes
# - Unspool things into alignment blocks (0th axis) and realigned stuff within the blocks
# - Flatten the index space downward, and trim the tail of the array away (assumed extra bits)


def _unpack_10bit(array: np.ndarray) -> np.ndarray:
    original_len = array.size
    array16 = array.reshape((-1, 5)).astype(np.uint16)

    unpacked_data = np.zeros((array16.shape[0], 4), dtype=np.uint16)
    # fmt: off
    unpacked_data[:, 0] = ((array16[:, 0] << 2) | (array16[:, 1] >> 6)) & 0x3FF
    unpacked_data[:, 1] = ((array16[:, 1] << 4) | (array16[:, 2] >> 4)) & 0x3FF
    unpacked_data[:, 2] = ((array16[:, 2] << 6) | (array16[:, 3] >> 2)) & 0x3FF
    unpacked_data[:, 3] = ((array16[:, 3] << 8) | (array16[:, 4]     )) & 0x3FF
    # fmt: on

    return unpacked_data.ravel()[: original_len * 4 // 5]


def _unpack_12bit(array: np.ndarray) -> np.ndarray:
    original_len = array.size
    array16 = array.reshape((-1, 3)).astype(np.uint16)

    unpacked_data = np.zeros((array16.shape[0], 2), dtype=np.uint16)
    # fmt: off
    unpacked_data[:, 0] = ((array16[:, 0] << 4) | (array16[:, 1] >> 4)) & 0xFFF
    unpacked_data[:, 1] = ((array16[:, 1] << 8) | (array16[:, 2]     )) & 0xFFF
    # fmt: on

    return unpacked_data.ravel()[: original_len * 2 // 3]


def round_up_to_multiple(value: int, multiple: int) -> int:
    return math.ceil(value / multiple) * multiple


def unpack_csi_padded(
    raw: np.ndarray, pixel_shape: Tuple[int, int], fmt: SensorFormat
) -> np.ndarray:
    """
    Args:
        raw: Flat uint8 array of bytes from the camera
        pixel_shape: the shape of the image in pixels (height, width)
        fmt:

    """
    _assert_is_byte_array(raw)
    assert fmt.packing == "CSI2P", "This method only treats CSI2P packing"

    # The Unicam (MIPI CSI?) series of sensors pad each row up to the nearest multiple of 32 bytes.
    # This is somewhat annoying to deal with, as we need also to also keep alignment
    # with the 10/12 bit packing.

    # 1. Compute the smallest nominal np array shape which meets the bit-alrignment requirements
    row_bit_length = fmt.bit_depth * pixel_shape[1]
    row_byte_length = round_up_to_multiple(row_bit_length, 8) // 8
    row_byte_length_padded = round_up_to_multiple(row_byte_length, 32)

    expected_data_length = row_byte_length_padded * pixel_shape[0]
    if raw.size != expected_data_length:
        raise ValueError(
            f"Raw data size {raw.size} does not match expected size {expected_data_length}"
        )

    n_rows = raw.size // row_byte_length_padded
    raw_rows = raw.reshape((-1, row_byte_length_padded))

    if fmt.bit_depth == 10:
        aligned_row_length = round_up_to_multiple(row_byte_length_padded, 5)
    if fmt.bit_depth == 12:
        aligned_row_length = round_up_to_multiple(row_byte_length_padded, 3)

    # 2. Copy the raw data into that array
    aligned_for_unpacking = np.zeros(
        (raw_rows.shape[0], aligned_row_length), dtype=np.uint8
    )
    aligned_for_unpacking[:, :row_byte_length_padded] = raw_rows

    # 3. Flatten and convert the byte-array into a uint16 array
    if fmt.bit_depth == 10:
        unpacked = _unpack_10bit(aligned_for_unpacking.ravel())
    if fmt.bit_depth == 12:
        unpacked = _unpack_12bit(aligned_for_unpacking.ravel())

    # 4. reshape the uint16 array into the desired shape
    unpacked_padded = unpacked.reshape((n_rows, -1))

    # 5. trim the tails of the horizontal lines away to the correct shape
    trimmed = unpacked_padded[:, : pixel_shape[1]]
    return trimmed


def unpack_raw(
    raw: np.ndarray, pixel_shape: Tuple[int, int], fmt: SensorFormat
) -> np.ndarray:
    """
    This converts a raw numpy byte array (flat, uint8) into a 2d numpy array of `pixel_shape`
    and dtype baed on SensorFormat. Note that in most formats this will still be a bayered image.
    """
    _assert_is_byte_array(raw)

    # TODO(meawoppl) - add other packed formats here
    if fmt.packing == "CSI2P":
        return unpack_csi_padded(raw, pixel_shape, fmt)
    else:
        raise RuntimeError(f"Unsupported bit raw format: {fmt}")

BayerLiterals = Literal["RGGB", "BGGR", "GRBG", "GBRG"]


def _bayer_masks(
    shape: Tuple[int, ...],
    pattern: BayerLiterals | str = "RGGB",
) -> Tuple[np.ndarray, ...]:
    """
    Return the mask array for red, green and blue masks for given pattern.

    shape - Dimensions of the bayered image
    pattern - Color filters on the pixel array.

    Returns a tuple of (r, g, b) masks
    """

    channel_index = {"R": 0, "G": 1, "B": 2}
    channels = list(np.zeros(shape, dtype="bool") for _ in range(3))
    for channel, (y, x) in zip(pattern, [(0, 0), (0, 1), (1, 0), (1, 1)]):
        channels[channel_index[channel]][y::2, x::2] = 1

    return channels



def debayer_bilinear(raw: np.ndarray, pattern: BayerLiterals | str="RGGB") -> np.ndarray:
    """
    Use a basic set of convolutions to debayer a raw image.
    """
    # Create empty arrays to hold the red, green, and blue channels.

    r_mask, g_mask, b_mask = _bayer_masks(raw.shape, pattern)

    g_kernel = np.array([
        [0, 1, 0],
        [1, 4, 1],
        [0, 1, 0],
    ], dtype=np.float32) / 4

    rb_kernel = np.array([
        [1, 2, 1],
        [2, 4, 2],
        [1, 2, 1],
    ], dtype=np.float32) / 4

    r_plane = convolve(raw * r_mask, rb_kernel)
    g_plane = convolve(raw * g_mask, g_kernel)
    b_plane = convolve(raw * b_mask, rb_kernel)

    rgb = np.empty((*raw.shape, 3), dtype=np.uint16)
    rgb[..., 0] = np.round(r_plane)
    rgb[..., 1] = np.round(g_plane)
    rgb[..., 2] = np.round(b_plane)

    return rgb