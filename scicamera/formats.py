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


def unpack_raw(array: np.ndarray, format: str) -> np.ndarray:
    """This converts a raw numpy byte array (flat, uint8) into a 2d numpy array

    Note that in most formats this will still be a bayered image.
    """
    assert array.dtype == np.uint8, "Raw unpack only accepts uint8 arrays"
    assert array.ndim == 1, "Unpack raw only accepts flat arrays"
    assert is_raw(format), "Passed format string does not represent a raw format"

    bit_depth = SensorFormat(format).bit_depth
    original_len = array.size

    # NOTE(meawoppl) - the below implementations are a bit memory inefficient when it comes
    # to deserialization of the 10/12 bit arrays, as it will overallocated by 1/5 and 1/3
    # respectively. This is a tradeoff for simplicity of implementation using numpy.
    # The approach breaks down to the following:
    # - Compute the number of bytes needed at which the data realigns itself to the next byte boundary
    #   - for 10 bit (4 pixels) - 40 bits, 5 bytes
    #   - fot 12 bit (2 pixels) - 24 bits, 3 bytes
    # - Unspool things into alignment blocks (0th axis) and realigned stuff within the blocks
    # - Flatten the index space downward, and trim the tail of the array away (assumed extra bits)

    if bit_depth == 8:
        return array
    elif bit_depth == 10:
        array16 = array.reshape((-1, 5)).astype(np.uint16)

        unpacked_data = np.zeros((array16.shape[0], 4), dtype=np.uint16)
        # fmt: off
        unpacked_data[:, 0] = ((array16[:, 0] << 2) | (array16[:, 1] >> 6)) & 0x3FF
        unpacked_data[:, 1] = ((array16[:, 1] << 4) | (array16[:, 2] >> 4)) & 0x3FF
        unpacked_data[:, 2] = ((array16[:, 2] << 6) | (array16[:, 3] >> 2)) & 0x3FF
        unpacked_data[:, 3] = ((array16[:, 3] << 8) | (array16[:, 4]     )) & 0x3FF
        # fmt: on

        return unpacked_data.ravel()[: original_len * 4 // 5]
    elif bit_depth == 12:
        array16 = array.reshape((-1, 3)).astype(np.uint16)

        unpacked_data = np.zeros((array16.shape[0], 2), dtype=np.uint16)
        # fmt: off
        unpacked_data[:, 0] = ((array16[:, 0] << 4) | (array16[:, 1] >> 4)) & 0xFFF
        unpacked_data[:, 1] = ((array16[:, 1] << 8) | (array16[:, 2]     )) & 0xFFF
        # fmt: on

        return unpacked_data.ravel()[: original_len * 2 // 3]
    else:
        raise RuntimeError(f"Unsupported bit depth: {bit_depth}")
