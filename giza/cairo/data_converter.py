# This module convert Data source to Cairo code.

from enum import Enum
import os
from typing import List
import numpy as np

from .file_manager import CairoData, ModFile


class FixedImpl(Enum):
    FP8x23 = 'FP8x23'
    FP16x16 = 'FP16x16'
    FP32x32 = 'FP32x32'


def to_fp(x: np.ndarray, fp_impl: FixedImpl):
    match fp_impl:
        case FixedImpl.FP8x23:
            return (x * 2**23).astype(np.int64)
        case FixedImpl.FP16x16:
            return (x * 2**16).astype(np.int64)
        case FixedImpl.FP32x32:
            return (x * 2**32).astype(np.int64)


class Dtype(Enum):
    FP32x32 = 'FP32x32'
    FP8x23 = 'FP8x23'
    FP16x16 = 'FP16x16'
    I8 = 'i8'
    I32 = 'i32'
    U32 = 'u32'


class Tensor:
    def __init__(self, dtype: Dtype, shape: tuple, data: np.ndarray):
        self.dtype = dtype
        self.shape = shape
        match dtype:
            case Dtype.FP8x23:
                self.data = to_fp(data.flatten(), FixedImpl.FP8x23)
            case Dtype.FP16x16:
                self.data = to_fp(data.flatten(), FixedImpl.FP16x16)
            case Dtype.FP32x32:
                self.data = to_fp(data.flatten(), FixedImpl.FP32x32)
            case _:
                self.data = data.flatten()


Sequence = List[Tensor]


class Trait(Enum):
    TENSOR = 'TENSOR'
    NN = 'NN'


def inputs_gen(inputs: list[Tensor | Sequence]):
    """
    Generate and write Cairo file based on the provided inputs .

    Args:
        inputs (list[Tensor | list[Tensor]]): A list of input tensors or tensor sequences.
        name (str): The name of the inputs file.
    """
    inputs_name = "inputs"

    ModFile().update(inputs_name)

    for i, input in enumerate(inputs):
        input_data = CairoData(os.path.join(inputs_name, f"input_{i}.cairo"))
        match input:
            case list():
                input_data.buffer = CairoData.sequence_template(
                    func=f"input_{i}",
                    dtype=input[0].dtype.value,
                    refs=get_data_refs(input[0].dtype),
                    data=get_data_statement_for_sequences(
                        input, input[0].dtype),
                    shape=[x.shape for x in input],
                )
            case Tensor():
                input_data.buffer = CairoData.base_template(
                    func=f"input_{i}",
                    dtype=input.dtype.value,
                    refs=get_data_refs(input.dtype),
                    data=get_data_statement(input.data, input.dtype),
                    shape=input.shape,
                )

        input_data.dump()


def get_data_refs(dtype: Dtype) -> list[str]:
    refs = [
        *trait_to_ref[Trait.TENSOR],
        *dtype_to_tensor[dtype],
        *dtype_to_numbers[dtype],
    ]

    return refs


def get_data_statement(data: np.ndarray, dtype: Dtype) -> list[str]:
    match dtype:
        case Dtype.U32:
            return [f"{int(x)}" for x in data.flatten()]
        case Dtype.I32:
            return ["i32 { "+f"mag: {abs(int(x))}, sign: {str(x < 0).lower()} "+"}" for x in data.flatten()]
        case Dtype.I8:
            return ["i8 { "+f"mag: {abs(int(x))}, sign: {str(x < 0).lower()} "+"}" for x in data.flatten()]
        case Dtype.FP8x23:
            return ["FP8x23 { "+f"mag: {abs(int(x))}, sign: {str(x < 0).lower()} "+"}" for x in data.flatten()]
        case Dtype.FP16x16:
            return ["FP16x16 { "+f"mag: {abs(int(x))}, sign: {str(x < 0).lower()} "+"}" for x in data.flatten()]


def get_data_statement_for_sequences(data: Sequence, dtype: Dtype) -> list[list[str]]:
    return [get_data_statement(x.data, dtype) for x in data]


trait_to_ref = {
    Trait.TENSOR: [
        "array::{ArrayTrait, SpanTrait}",
        "orion::operators::tensor::{TensorTrait, Tensor}",
    ],
    Trait.NN: [
        "orion::numbers::FixedTrait",
        "orion::operators::nn::NNTrait",
    ],
}

dtype_to_tensor = {
    Dtype.U32: ["orion::operators::tensor::U32Tensor",],
    Dtype.I32: ["orion::operators::tensor::I32Tensor",],
    Dtype.I8: ["orion::operators::tensor::I8Tensor",],
    Dtype.FP8x23: ["orion::operators::tensor::FP8x23Tensor",],
    Dtype.FP16x16: ["orion::operators::tensor::FP16x16Tensor",],
}

dtype_to_numbers = {
    Dtype.U32: [],
    Dtype.I32: ["orion::numbers::{IntegerTrait, i32}",],
    Dtype.I8: ["orion::numbers::{IntegerTrait, i8}",],
    Dtype.FP8x23: ["orion::numbers::{FixedTrait, FP8x23}",],
    Dtype.FP16x16: ["orion::numbers::{FixedTrait, FP16x16}",],
}