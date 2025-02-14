from typing import Tuple

from . import operators
from .autodiff import Context
from .fast_ops import FastOps
from .tensor import Tensor
from .tensor_functions import Function, rand, tensor


# List of functions in this file:
# - avgpool2d: Tiled average pooling 2D
# - argmax: Compute the argmax as a 1-hot tensor
# - Max: New Function for max operator
# - max: Apply max reduction
# - softmax: Compute the softmax as a tensor
# - logsoftmax: Compute the log of the softmax as a tensor - See https://en.wikipedia.org/wiki/LogSumExp#log-sum-exp_trick_for_log-domain_calculations
# - maxpool2d: Tiled max pooling 2D
# - dropout: Dropout positions based on random noise, include an argument to turn off


def tile(input: Tensor, kernel: Tuple[int, int]) -> Tuple[Tensor, int, int]:
    """Reshape an image tensor for 2D pooling

    Args:
    ----
        input: batch x channel x height x width
        kernel: height x width of pooling

    Returns:
    -------
        Tensor of size batch x channel x new_height x new_width x (kernel_height * kernel_width) as well as the new_height and new_width value.

    """
    batch, channel, height, width = input.shape
    kh, kw = kernel
    assert height % kh == 0
    assert width % kw == 0

    new_height = height // kh
    new_width = width // kw

    # First reshape to (B, C, new_height, kh, new_width, kw)
    t = input.view(batch, channel, new_height, kh, new_width, kw).contiguous()
    # Permute to (B, C, new_height, new_width, kh, kw)
    t = t.permute(0, 1, 2, 4, 3, 5).contiguous()
    # Flatten the kernel dimensions: (B, C, new_height, new_width, kh*kw)
    t = t.view(batch, channel, new_height, new_width, kh * kw)
    return t, new_height, new_width


# TODO: Implement for Task 4.3.
def avgpool2d(input: Tensor, kernel: Tuple[int, int]) -> Tensor:
    """Tiled average pooling 2D.

    Args:
        input: Tensor of shape (batch, channel, height, width).
        kernel: Tuple (kh, kw) for the pooling kernel dimensions.

    Returns:
        A tensor of shape (batch, channel, new_height, new_width) where
        each output element is the average of a kernel window.
    """
    tiled, new_height, new_width = tile(input, kernel)
    kh, kw = kernel
    pool_area = kh * kw
    # Sum over the kernel window (dimension 4) then squeeze that dimension.
    return tiled.sum(dim=4) / pool_area


def dropout(
    input: Tensor, p: float, train: bool = True, ignore: bool = False
) -> Tensor:
    """Apply dropout to the input tensor.

    Args:
        input: The input tensor.
        p: Dropout probability (fraction of elements to drop).
        train: If False, dropout is turned off.
        ignore: If True, dropout is ignored.

    Returns:
        The tensor after applying dropout.
    """
    if ignore or (not train) or p == 0:
        return input
    if p == 1.0:
        return input.zeros(input.shape)
    noise = rand(input.shape, backend=input.backend)
    mask = noise > p
    return input * mask / (1.0 - p)
