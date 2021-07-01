import ipywidgets as ipyw
import traitlets as trt
import typing as ty

from ipywidgets.widgets.trait_types import TypedTuple

from ..core import Base


@ipyw.register
class BaseWidget(Base, ipyw.DOMWidget):
    """A base widget to enforce standardization with selectors."""

    description = trt.Unicode("Unnamed Widget").tag(sync=True)
    selected: ty.Tuple[str] = ipyw.widgets.trait_types.TypedTuple(
        trait=trt.Unicode(),
    ).tag(sync=True)

    def update_selected(self, *new_selections: str):
        if set(self.selected).symmetric_difference(new_selections):
            self.selected = new_selections
