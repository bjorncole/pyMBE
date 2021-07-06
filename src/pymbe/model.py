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
            item._data["name"]: item
            for item in self
            if isinstance(item, Element)
            and "name" in item._data
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

        data = element._data
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

    name: str = "SysML v2 Model"

    all_relationships: Dict[str, "Element"] = field(default_factory=dict)
    all_non_relationships: Dict[str, "Element"] = field(default_factory=dict)

    ownedElement: ListGetter = field(default_factory=ListGetter)
    ownedMetatype: Dict[str, List["Element"]] = field(default_factory=dict)
    ownedRelationship: List["Element"] = field(default_factory=list)

    source: Any = None

    _naming: Naming = Naming.long  # The scheme to use for repr'ing the elements

    def __post_init__(self):
        self.elements = {
            id_: Element(_data=data, _model=self)
            for id_, data in self.elements.items()
        }
        self._add_relationships()
        self._add_owned()

        self.all_relationships = {
            id_: element
            for id_, element in self.elements.items()
            if element._is_relationship
        }
        self.all_non_relationships = {
            id_: element
            for id_, element in self.elements.items()
            if not element._is_relationship
        }

    def __repr__(self) -> str:
        data = self.source or f"{len(self.elements)} elements"
        return f"<SysML v2 Model ({data})>"

    @staticmethod
    def load(
        elements: Union[List[Dict], Set[Dict], Tuple[Dict]],
        **kwargs,
    ) -> "Model":
        """Make a Model from an iterable container of elements"""
        return Model(
            elements={
                element["@id"]: element
                for element in elements
            },
            **kwargs,
        )

    @staticmethod
    def load_from_file(filepath: Union[Path, str]) -> "Model":
        """Make a model from a JSON file"""
        if isinstance(filepath, str):
            filepath = Path(filepath)

        if not filepath.is_file():
            raise ValueError(f"'{filepath}' does not exist!")

        return Model.load(
            elements=json.loads(filepath.read_text()),
            name=filepath.name,
            source=filepath.resolve(),
        )

    def save_to_file(self, filepath: Union[Path, str]) -> bool:
        if isinstance(filepath, str):
            filepath = Path(filepath)
        filepath.write_text(
            json.dumps(
                [element._data for element in self.elements.values()],
                indent=2,
            ),
        )

    def _add_relationships(self):
        """Adds relationships to elements"""
        for element in self.elements.values():
            if not element._is_relationship:
                continue
            endpts = [
                # TODO: should this handle multiple sources and/or targets?
                self.elements[element._data[endpoint][0]["@id"]]
                for endpoint in ("source", "target")
            ]
            metatype = element._metatype
            endpts[0]._derived[f"through{metatype}"] += [{"@id": endpts[1]._data["@id"]}]
            endpts[1]._derived[f"reverse{metatype}"] += [{"@id": endpts[0]._data["@id"]}]

    def _add_owned(self):
        """Adds owned elements, relationships, and metatypes to the model"""
        elements = tuple(self.elements.values())

        owned = [
            element
            for element in elements
            if element._data.get("owner") is None
        ]
        self.ownedElement = ListGetter(
            element
            for element in owned
            if not element._is_relationship
        )

        self.ownedRelationship = [
            relationship
            for relationship in owned
            if relationship._is_relationship
        ]

        by_metatype = defaultdict(list)
        for element in elements:
            by_metatype[element._metatype].append(element)
        self.ownedMetatype = dict(by_metatype)


@dataclass(repr=False)
class Element:
    """A SysML v2 Element"""

    _data: dict
    _model: Model

    _derived: Dict[str, List] = field(default_factory=lambda: defaultdict(list))
    _is_relationship: bool = False

    def __post_init__(self):
        self._is_abstract = bool(self._data.get("isAbstract"))
        self._is_relationship = "relatedElement" in self._data
        self._data["ownedElement"] = ListGetter(self._data["ownedElement"])

    def __dir__(self):
        return sorted(
            list(super().__dir__()) + [
                key
                for key in [*self._data, *self._derived]
                if key.isidentifier()
            ]
        )

    def __getattr__(self, key: str):
        try:
             return self.__getattribute__(key)
        except AttributeError as exc:
            try:
                return self[key]
            except KeyError:
                if key.startswith("_"):
                    try:
                        return self[f"@{key[1:]}"]
                    except KeyError:
                        pass
            raise exc

    @lru_cache
    def __getitem__(self, key: str):
        found = False
        for source in ("_data", "_derived"):
            source = self.__getattribute__(source)
            if key in source:
                found = True
                item = source[key]
                break
        if not found:
            raise KeyError(f"No '{key}' in {self}")

        if isinstance(item, (dict, str)):
            item = self.__safe_dereference(item)
        elif isinstance(item, (list, tuple, set)):
            items = [
                self.__safe_dereference(subitem)
                for subitem in item
            ]
            # TODO: Add attribute to model to control returning item of single-item lists
            if (
                len(items) == 1 and
                not (isinstance(key, str) and key.startswith("owned")) and
                key not in ("input",)  # TODO: add all keys that should not be flattened
            ):
                return items[0]
            return type(item)(items)
        return item

    def __hash__(self):
        return hash(self._data["@id"])

    def __repr__(self):
        return self._model._naming.get_name(element=self)

    @property
    def _id(self):
        return self._data["@id"]

    @property
    def _metatype(self):
        return self._data["@type"]

    @property
    def relationships(self):
        return {key: self[key] for key in self._derived}

    def create(data: dict, model: Model) -> "Element":
        return Element(_data=data, _model=model)

    def __safe_dereference(self, item):
        """If given a reference to another element, try to get that element"""
        try:
            if isinstance(item, dict) and "@id" in item:
                if len(item) > 1:
                    warn("Found a reference with more than one entry: {item}")
                item = item["@id"]
            return self._model.elements[item]
        except KeyError:
            return item


@dataclass
class Instance:
    """An M0 instantiation of an element"""

    element: Element
