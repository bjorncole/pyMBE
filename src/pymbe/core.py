import traitlets as trt
import typing as ty


class Base(trt.HasTraits):
    """A common base class to standardize properties and interactions"""

    elements_by_id: ty.Dict[str, dict] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Dict(),
    )
