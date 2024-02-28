use orion::operators::tensor::{Tensor, TensorTrait};
use orion::operators::tensor::{U32Tensor, I32Tensor, I8Tensor, FP8x23Tensor, FP16x16Tensor, FP32x32Tensor, BoolTensor};
use orion::numbers::{FP8x23, FP16x16, FP32x32};
use orion::operators::matrix::{MutMatrix, MutMatrixImpl};
use orion::operators::nn::{NNTrait, FP16x16NN};

use node_linear1_weight::get_node_linear1_weight;
use node_linear1_bias::get_node_linear1_bias;
use node_linear2_weight::get_node_linear2_weight;
use node_linear2_bias::get_node_linear2_bias;
use node_linear3_weight::get_node_linear3_weight;
use node_linear3_bias::get_node_linear3_bias;

use _constant_value::get__constant_value;

fn main(node_onnx_reshape_0: Tensor<FP16x16>) -> Tensor<FP16x16> {
let node__constant_output_0 = get__constant_value();
let node__reshape_output_0 = TensorTrait::reshape(@node_onnx_reshape_0, node__constant_output_0.data);
let node__linear1_gemm_output_0 = NNTrait::gemm(node__reshape_output_0, get_node_linear1_weight(), Option::Some(get_node_linear1_bias()), Option::Some(FP16x16 { mag: 65536, sign: false }), Option::Some(FP16x16 { mag: 65536, sign: false }), false, true);
let node__relu_relu_output_0 = NNTrait::relu(@node__linear1_gemm_output_0);
let node__linear2_gemm_output_0 = NNTrait::gemm(node__relu_relu_output_0, get_node_linear2_weight(), Option::Some(get_node_linear2_bias()), Option::Some(FP16x16 { mag: 65536, sign: false }), Option::Some(FP16x16 { mag: 65536, sign: false }), false, true);
let node__relu_1_relu_output_0 = NNTrait::relu(@node__linear2_gemm_output_0);
let node_13 = NNTrait::gemm(node__relu_1_relu_output_0, get_node_linear3_weight(), Option::Some(get_node_linear3_bias()), Option::Some(FP16x16 { mag: 65536, sign: false }), Option::Some(FP16x16 { mag: 65536, sign: false }), false, true);

        node_13
    }