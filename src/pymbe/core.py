import typing as ty
import warnings

import traitlets as trt


class Base(trt.HasTraits):
    """A common base class to standardize properties and interactions"""

    elements_by_id: ty.Dict[str, dict] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Dict(),
    )
    elements_by_type: ty.Dict[str, ty.Tuple[str]] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Tuple(),
    )

    def update(self, elements: dict):
        """Subclasses must implement this!"""
        warnings.warn(
            f"{self.__class__.__name__} does not "
            f"specialize the `update` method!"
        )

    def get_element_by_id(self, id_: str) -> dict:
        return self.elements_by_id[id_]

    def get_name_by_id(self, id_: str) -> str:
        return self.get_element_by_id(id_).get("name")

    @trt.observe("elements_by_id")
    def _update_elements(self, *_):
        elements = tuple(self.elements_by_id.values())
        element_types = {element["@type"] for element in elements}
        self.elements_by_type = {
            element_type: tuple([
                element["@id"]
                for element in elements
                if element["@type"] == element_type
            ])
            for element_type in element_types
        }
        self.update(elements=self.elements_by_id)
