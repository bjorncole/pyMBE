from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Mapper:
    """Facilitate the finding of uniquely mapped elements."""

    to_map: dict = field(repr=False)
    from_map: dict = field(default=None, repr=False)
    unified_map: dict = field(default=None, repr=False)

    def __len__(self):
        return len(self.to_map)

    def __repr__(self):
        return f"Mapper({len(self.to_map)} Items)"

    def __post_init__(self, *args, **kwargs):
        # Filter out missing
        self.to_map = {
            source: target
            for source, target in self.to_map.items()
            if target is not None
        }
        if not self.from_map:
            self.from_map = {v: k for k, v in self.to_map.items()}

        common_keys = set(self.from_map).intersection(self.to_map)
        if common_keys:
            raise ValueError(f"Found common keys in the mapper: {common_keys}")

        self.unified_map = self.to_map.copy()
        self.unified_map.update(self.from_map)

    def get(self, *items):
        return [
            self.unified_map[item]
            for item in items
            if item in self.unified_map
        ]


class VisibilityKind(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PACKAGE = "package"
