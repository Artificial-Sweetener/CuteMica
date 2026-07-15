"""Portable reconstruction of Mica's quarter-scale speed blur kernel."""

from __future__ import annotations

from base64 import b85decode
from functools import lru_cache
from typing import Literal
from zlib import decompress

import numpy as np

from cutemica.core.float_blur import FloatPixels

SPEED_BLUR_RADIUS_PIXELS = 30.0
SPEED_BLUR_SUPPORT_PIXELS = 81
_RADIUS = SPEED_BLUR_SUPPORT_PIXELS
_PERIOD = 9
_CONSTANT_GAIN = np.float32(255.0 / 256.0)
_HORIZONTAL_SAMPLE_OFFSET = np.float32(0.75)
_ENCODED_KERNELS = (
    "c-rmNxla>d7{~GVeV+Gv-q(Q^TAb9uW096aCpGby1m&32#AA|*fRmbdOj4lWq$VB{R0N&W#A6"
    "Xq&`C`cCn=ONse{J^1&WF9UI&&EWBUCA-sF9T&yTTUtCeOO*=}}}U0^ra6ZV09XFM;%H}O6E7{ADG@"
    "u&PF|G^11!(KQJm*6%$g9-Qvn3u&ZxDQX@WxRvW@e}?+v4Vc%EWW`9coolJ6K=<~`48hVWZ*U2hhA"
    "uhM%V`BkmECaoDcCH-o_hv4G-skf-kW&8)Jhk!CF~8t7f4B-lqg=p#xsP98_Qo`!R(<aX@s65s?*9*"
    "&^@CX<4S~RkwPn7FCsQ)%Wy_4x2{PW5!I*)KEJO(JTdQ#Mato+hP0dh@G_aHt3?R&c$5ZCEch?xvZ"
    "0GzPb1AvAf~UyCZIw+u(%zYTwyM_PRZ158It~y<Mhp>ZK+sr;HgiZKm2R=~p_T8+1sg)qpy!D%FA<"
    "m0j|nER|CtDNc!qn8#s^V;u%?68fMSwifWt#flaCKNe&qdlB%i#Jw-`81dF5#gr)Z_H=oJ7G$OOXh"
    "5Y^$orJ=PA%zbZ`Pp6m=da>{dAJ9P#+D`XPWzqkS?!$57B<1xAc&%(OEh~J7^u{yt_T#->{kS7P"
    "smuz36T3_C}YfY43H5jLNL{yVE-!6e(|d3@cW&M1|X()m-Yr?Q(HJ{*C?sqsiqo"
)


def speed_blur_pixels(pixels: FloatPixels) -> FloatPixels:
    """Apply CuteMica's sigma-30 speed kernel with reflected boundaries."""

    blurred = _blur_axis(pixels, axis=1)
    blurred = _blur_axis(blurred, axis=0)
    right = np.concatenate((blurred[:, 1:], blurred[:, -1:]), axis=1)
    shifted = blurred * (1.0 - _HORIZONTAL_SAMPLE_OFFSET)
    shifted += right * _HORIZONTAL_SAMPLE_OFFSET
    return shifted


def _blur_axis(
    pixels: FloatPixels,
    axis: Literal[0, 1],
) -> FloatPixels:
    padding = [(0, 0), (0, 0), (0, 0)]
    padding[axis] = (_RADIUS, _RADIUS)
    padded = np.pad(pixels, padding, mode="reflect")
    working = np.swapaxes(padded, 0, 1) if axis == 0 else padded
    height, width, _channels = working.shape
    transform_size = 1 << (width + 2 * _RADIUS - 1).bit_length()
    result = np.zeros_like(working)
    indices = np.arange(width)
    for phase, spectrum in _kernel_spectra(transform_size):
        selected = (indices - _RADIUS) % _PERIOD == phase
        phase_pixels = np.zeros_like(working)
        phase_pixels[:, selected] = working[:, selected]
        transformed = np.fft.rfft(phase_pixels, n=transform_size, axis=1)
        convolution = np.fft.irfft(
            transformed * spectrum[None, :, None],
            n=transform_size,
            axis=1,
        )
        result += convolution[:, _RADIUS : _RADIUS + width].astype(np.float32)
    restored = np.swapaxes(result, 0, 1) if axis == 0 else result
    slices = [slice(None), slice(None), slice(None)]
    slices[axis] = slice(_RADIUS, -_RADIUS)
    return restored[tuple(slices)]


@lru_cache(maxsize=8)
def _kernel_spectra(
    transform_size: int,
) -> tuple[tuple[int, np.ndarray], ...]:
    kernels = np.frombuffer(
        decompress(b85decode(_ENCODED_KERNELS)),
        dtype=np.uint16,
    ).reshape(_PERIOD, 2 * _RADIUS + 1)
    spectra: list[tuple[int, np.ndarray]] = []
    for phase, quantized in enumerate(kernels):
        if not np.any(quantized):
            continue
        weights = quantized.astype(np.float32) / np.float32(65535.0)
        weights *= _CONSTANT_GAIN
        spectrum = np.fft.rfft(weights, n=transform_size).astype(np.complex64)
        spectra.append((phase, spectrum))
    return tuple(spectra)
