import ipywidgets as ipyw
import traitlets as trt
import typing as ty

from ..core import Base


class BaseWidget(Base, ipyw.DOMWidget):
    """A base widget to enforce standardization with selectors."""

    description = trt.Unicode("Unnamed Widget").tag(sync=True)
    selected: ty.Tuple[str] = trt.Tuple()
