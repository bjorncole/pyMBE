import json

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union
from warnings import warn


class ListGetter(list):
    """A list that also can return items by their name."""

    def __getitem__(self, key):
        item_map = {
            item.name: item
            for item in self
            if item.name
        }
        if key in item_map:
            return item_map[key]
        return super().__getitem__(key)


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

    # TODO: Look into making elements immutable (e.g., frozen dict)
    elements: Dict[str, "Element"]

    ownedElement: ListGetter = field(default_factory=ListGetter)
    ownedRelationship: List["Element"] = field(default_factory=list)
    ownedMetatypes: Dict[str, List["Element"]] = field(default_factory=dict)

    source: Any = None

    _naming: Naming = Naming.long

    def __post_init__(self):
        self.elements = {
            id_: Element(data=data, model=self)
            for id_, data in self.elements.items()
        }
        self._add_relationships()
        self._add_owned()

    def __repr__(self) -> str:
        data = self.source or f"{len(self.elements)} elements"
        return f"<SysML v2 Model ({data})>"

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

    @staticmethod
    def load_from_file(filepath: Union[Path, str]) -> "Model":
        """Make a model from a JSON file"""
        if isinstance(filepath, str):
            filepath = Path(filepath)

        if not filepath.exists():
            raise ValueError(f"'{filepath}' does not exist!")

        return Model.load(
            elements=json.loads(filepath.read_text()),
            source=filepath.resolve(),
        )

    def _add_relationships(self):
        """Adds relationships to elements"""
        for element in self.elements.values():
            if not element._is_relationship:
                continue
            metatype = element._metatype
            source, target = element.source, element.target

            source._derived[f"through{metatype}"] += [{"@id": target.data["@id"]}]
            target._derived[f"reverse{metatype}"] += [{"@id": source.data["@id"]}]

    def _add_owned(self):
        """Adds owned elements, relationships, and metatypes to the model"""
        elements = tuple(self.elements.values())

        owned = [
            element
            for element in elements
            if element.data.get("owner") is None
        ]
        self.ownedElement = ListGetter(el for el in owned if not el._is_relationship)

        self.ownedRelationship = [
            rel for rel in owned if rel._is_relationship
        ]

        by_metatype = defaultdict(list)
        for element in elements:
            # FIXME: figure out why we can't do this in the Element's __post_init__
            element.ownedElement = ListGetter(element.ownedElement)

            by_metatype[element._metatype] = element

        self.ownedMetatypes = dict(by_metatype)


@dataclass(repr=False)
class Element:
    """A SysML v2 Element"""

    data: dict
    model: Model

    _derived: Dict[str, List] = field(default_factory=lambda: defaultdict(list))
    _is_relationship: bool = False

    def __post_init__(self):
        self._is_relationship = "relatedElement" in self.data

    def __dir__(self):
        return sorted(
            [key for key in self.data if key.isidentifier()] +
            [key for key in self._derived if key.isidentifier()] +
            list(super().__dir__())
        )

    def __getattr__(self, key: str):
        if key.startswith("_") and f"@{key[1:]}" in self.data:
            key = f"@{key[1:]}"
        possibilities = [*self.data, *self._derived]
        if key in possibilities:
            return self[key]
        return self.__getattribute__(key)

    @lru_cache
    def __getitem__(self, key: str):
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
