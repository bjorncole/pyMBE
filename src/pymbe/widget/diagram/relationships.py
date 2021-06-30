from enum import Enum
from pydantic import Field

from ipyelk.elements import Edge, EdgeProperties, Label

from .parts import PartMetadata


class RelationEndKind(Enum):
    HEAD = "head"
    TAIL = "tail"


# class RelationEnd(elements.BaseElement):
#     kind: RelationEndKind = None
#     multiplicity: ty.Tuple[int, int] = tuple((None, None))
#     name: str = None
#     attributes: ty.List[str] = None


class Relationship(Edge):
    # source_end: RelationEnd = None
    # target_end: RelationEnd = None
    display_kind: bool = True
    display_multiplicity: bool = True
    display_usage: bool = True
    data: dict = Field(default_factory=dict)

    @staticmethod
    def from_metatype(metatype):
        return METATYPE_TO_RELATIONSHIP_TYPES.get(
            metatype,
            DirectedAssociation,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        id_ = self.data["@id"]
        metatype = self.data.get("@type")
        if id_.startswith("_") or self.data.get("implied"):
            self.add_class("dashed")
        if metatype:
            self.labels.append(Label(text=f"«{metatype}»"))
        self.metadata = PartMetadata(sysml_id=id_)

        # TODO: Add processing of relationship properties
        # if self.display_kind and self.kind:
        #     self.labels += [ElkLabel(
        #         text=f"«{self.kind}»",
        #         id=f"{self.identifier}_label",
        #     )]

        # if self.display_multiplicity and self.multiplicity:
        #     mid = "" if None in self.multiplicity else ".."

        #     lower, upper = self.multiplicity

        #     lower = self.multiplicity[0] or "0"
        #     upper = self.multiplicity[1] or "*"
        #     self.labels += [ElkLabel(
        #         id=f"{self.id}_label_tail",
        #         text=f"{lower}{mid}{upper}",
        #         layoutOptions={
        #             "org.eclipse.elk.edgeLabels.placement": "TAIL",
        #         },
        #     )]

        # if self.display_usage and self.usage:
        #     self.labels += [ElkLabel(
        #         id=f"{self.id}_label_tail",
        #         text=f"{{{self.usage}}}",
        #         layoutOptions={
        #             "org.eclipse.elk.edgeLabels.placement": "HEAD",
        #         },
        #     )]


class Aggregation(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"start": "aggregation"})


class Association(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"end": "association"})


class Composition(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"start": "composition"})


class Containment(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"start": "containment"})


class DirectedAssociation(Relationship):
    properties: EdgeProperties = EdgeProperties(
        shape={"end": "directed_association"},
    )


class FeatureTyping(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"end": "feature_typing"})


class Generalization(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"end": "generalization"})


class OwnedBy(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"end": "containment"})


class Redefinition(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"end": "redefinition"})


class Subsetting(Relationship):
    properties: EdgeProperties = EdgeProperties(shape={"end": "subsetting"})


METATYPE_TO_RELATIONSHIP_TYPES = {
    "FeatureTyping": FeatureTyping,
    "OwnedBy": OwnedBy,
    "Redefinition": Redefinition,
    "Subsetting": Subsetting,
    "Superclassing": Generalization,
    # TODO: review and map the rest of the edge types
}
