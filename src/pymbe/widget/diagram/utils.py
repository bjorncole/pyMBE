from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from traitlets.traitlets import default


@dataclass
class Mapper:
    """Facilitate the finding of SysML and ELKJS elements."""

    to_sysml: dict = field(repr=False)
    to_elkjs: dict = field(default=None, repr=False)
    unified_map: dict = field(default=None, repr=False)
    unique: bool = field(default=True, repr=False)

    def __len__(self):
        return len(self.to_sysml)

    def __repr__(self):
        return f"Mapper({len(self.to_sysml)} Items)"

    def __post_init__(self, *args, **kwargs):
        # Filter maps with no SysML ID
        self.to_sysml = {
            elkjs_id: sysml_id
            for elkjs_id, sysml_id in self.to_sysml.items()
            if sysml_id is not None
        }

        common_keys = set(self.to_sysml).intersection(self.to_sysml.values())
        if common_keys:
            self.unique = False
            self.to_elkjs = defaultdict(list)
            for elkjs_id, sysml_id in self.to_sysml.items():
                self.to_elkjs[sysml_id] += [elkjs_id]
            self.to_sysml = {
                elkjs_id: [sysml_id]
                for elkjs_id, sysml_id in self.to_sysml.items()
            }
            self.unified_map = self.to_elkjs.copy()
            for elkjs_id, sysml_ids in self.to_sysml.items():
                self.unified_map[elkjs_id] += sysml_ids
        elif not self.to_elkjs:
            self.to_elkjs = {
                sysml_id: elkjs_id
                for elkjs_id, sysml_id in self.to_sysml.items()
            }

        if not common_keys:
            self.unified_map = {**self.to_sysml, **self.to_elkjs}

    def get(self, *items):
        results = [
            self.unified_map[item]
            for item in items
            if item in self.unified_map
        ]
        if not self.unique:
            results = sum(results, [])
        return tuple(set(results))


class VisibilityKind(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PACKAGE = "package"
