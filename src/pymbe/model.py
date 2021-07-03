import json

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union
from warnings import warn


class Naming(Enum):
    """An enumeration for how to repr SysML elements"""

    identifier = "IDENTIFIER"
    long = "LONG"
    qualified = "QUALIFIED"
    short = "SHORT"

    def get_name(self, element: "Element") -> str:
        naming = self._value_

        # TODO: Check with Bjorn, he wanted: (a)-[r:RELTYPE {name: a.name + '<->' + b.name}]->(b)
        if element._is_relationship:
            return (
                f"<{element._metatype}({element.source} ←→ {element.target})>"
            )

        data = element.data
        if naming == Naming.qualified:
            return f"""<{data["qualifiedName"]}>"""

        if naming == Naming.identifier:
            return f"""<{data["@id"]}>"""

        name = data.get("name") or data["@id"]
        if naming == Naming.short:
            return f"<{name}>"
        else:
            return f"""<{name} «{data["@type"]}»>"""


@dataclass(repr=False)
class Model:
    """A SysML v2 Model"""

    elements: dict  # TODO: Look into making this immutable (frozen dict?)
    source: Any = field(default_factory=str)

    _naming: Naming = Naming.long
    _owned_elements: Dict[str, "Element"] = field(default_factory=dict)
    _owned_relationships: List["Element"] = field(default_factory=list)

    @staticmethod
    def load(
        elements: Union[List[Dict], Set[Dict], Tuple[Dict]],
        source: str = "",
    ) -> "Model":
        """Make a Model from an iterable container of elements"""
        return Model(
            elements={
                element["@id"]: element
                for element in elements
            },
            source=source,
        )

    def __post_init__(self):
        self.elements = {
            id_: Element(data=data, model=self)
            for id_, data in self.elements.items()
        }
        self._add_relationships()
        self._add_owned()

    def __getattr__(self, key):
        if key in self._owned_elements:
            return self._owned_elements[key]
        return self.__getattribute__(key)

    def __repr__(self) -> str:
        data = self.source or f"len(self.elements) elements"
        return f"<SysML v2 Model ({data})>"

    @staticmethod
    def load_from_file(filepath: Union[Path, str]) -> "Model":
        """Make a model from a file"""
        if isinstance(filepath, str):
            filepath = Path(filepath)

        if not filepath.exists():
            raise ValueError(f"'{filepath}' does not exist!")

        return Model.load(
            elements=json.loads(filepath.read_text()),
            source=str(filepath.resolve()),
        )

    @staticmethod
    def load_from_api() -> "Model":
        raise NotImplementedError("""Need to implement this""")

    def _add_relationships(self):
        for element in self.elements.values():
            if not element._is_relationship:
                continue
            metatype = element._metatype
            source, target = element.source, element.target

            source._derived[f"through{metatype}"] += [{"@id": target.data["@id"]}]
            target._derived[f"reverse{metatype}"] += [{"@id": source.data["@id"]}]

    def _add_owned(self):
        # Add owned by others
        for element in self.elements.values():
            element._owned_elements = {
                child.name.replace(" ", "_"): child
                for child in element.ownedElement
                if child.name
            }

        # Add owned by model
        owned = [
            element
            for element in self.elements.values()
            if element.data.get("owner") is None
        ]
        owned_elements = [el for el in owned if not el._is_relationship]
        self._owned_elements = {
            element.data["name"]: element
            for element in owned_elements
        }
        if len(self._owned_elements) < len(owned_elements):
            warn("Model has duplicated directly owned elements")
        self._owned_elements = dict(sorted(self._owned_elements.items()))

        self._owned_relationships = tuple(
            rel for rel in owned if rel._is_relationship
        )


@dataclass(repr=False)
class Element:
    """A SysML v2 Element"""

    data: dict
    model: Model

    _derived: Dict[str, List] = field(default_factory=lambda: defaultdict(list))
    _is_relationship: bool = False
    _owned_elements: Dict[str, "Element"] = field(default_factory=dict)

    def __post_init__(self):        
        self._is_relationship = "relatedElement" in self.data

    def __dir__(self):
        return sorted(
            [name for name in self._owned_elements if name.isidentifier()] +
            [key for key in self.data if key.isidentifier()] +
            [key for key in self._derived if key.isidentifier()] +
            list(super().__dir__())
        )

    def __getattr__(self, key: str):
        if key.startswith("_") and f"@{key[1:]}" in self.data:
            key = f"@{key[1:]}"
        possibilities = [*self.data, *self._derived, *self._owned_elements]
        if key in possibilities:
            return self[key]
        return self.__getattribute__(key)

    @lru_cache
    def __getitem__(self, key: str):
        if key in self._owned_elements:
            return self._owned_elements[key]

        if key in self.data:
            item = self.data[key]
        else:
            item = self._derived[key]

        if isinstance(item, (list, tuple, set)):
            if all(
                (
                    isinstance(subitem, dict)
                    and "@id" in subitem
                    and len(subitem) < 2
                )
                for subitem in item
            ):
                items = [
                    self.model.elements[subitem["@id"]]
                    for subitem in item
                ]
                if not key.startswith("owned") and len(items) == 1:
                    return items[0]
                return type(item)(items)

        if isinstance(item, dict) and "@id" in item and len(item) < 2:
            item = item["@id"]

        if item in self.model.elements:
            return self.model.elements[item]

        return item

    def __hash__(self):
        return hash(self.data["@id"])

    def __repr__(self):
        return self.model._naming.get_name(element=self)

    @property
    def _id(self):
        return self.data["@id"]

    @property
    def _metatype(self):
        return self.data["@type"]

    @property
    def relationships(self):
        return {key: self[key] for key in self._derived}
