mod chunk0;

use orion::operators::tensor::{U32Tensor, Tensor, TensorTrait};


fn get__constant_value() -> Tensor<u32> {
    let mut shape = array![2];

    let mut data = array![];
     chunk0::compute(ref data);

    TensorTrait::new(shape.span(), data.span())
}