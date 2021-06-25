from pydantic import Field
from typing import Dict, Type, Union

from ipyelk.elements import (
    Edge,
    Node,
    Partition,
    Port,
    SymbolSpec,
    merge_excluded,
)

from .relationships import DirectedAssociation, Relationship
from .symbols import (
    make_arrow_symbol,
    make_containment_symbol,
    make_feature_typing_symbol,
    make_redefinition_symbol,
    make_rhombus_symbol,
    make_subsetting_symbol,
)


class PartDiagram(Partition):
    """A SysML 2 Part Diagram, based on the IPyELK BlockDiagram."""

    class Config:
        copy_on_model_validation = False
        excluded = merge_excluded(Partition, "symbols", "style")

    default_edge: Type[Edge] = Field(default=DirectedAssociation)

    symbols: SymbolSpec = SymbolSpec().add(
        make_arrow_symbol(identifier="generalization", r=8, closed=True),
        make_arrow_symbol(identifier="directed_association", r=8, closed=False),
        make_containment_symbol(identifier="containment", r=8),
        make_feature_typing_symbol(identifier="feature_typing", r=8),
        make_redefinition_symbol(identifier="redefinition", r=8),
        make_subsetting_symbol(identifier="subsetting", r=8),
        make_rhombus_symbol(identifier="composition", r=8),
        make_rhombus_symbol(identifier="aggregation", r=8),
    )

    style: Dict[str, Dict] = {
        # Elk Label styles for Box Titles
        " .elklabel.compartment_title_1": {
            "font-style": "normal",
            "font-weight": "normal",
        },
        " .elklabel.compartment_title_2": {
            "font-style": "normal",
            "font-weight": "bold",
        },
        # Style Arrowheads (future may try to )
        " .subsetting > .round > ellipse": {
            "fill": "var(--jp-elk-node-stroke)",
        },
        " .feature_typing > .round > ellipse": {
            "fill": "var(--jp-elk-node-stroke)",
        },
        " .internal > .elknode": {
            "stroke": "transparent",
            "fill": "transparent",
        },
        # Necessary for having the viewport use the whole vertical height
        " .lm-Widget.jp-ElkView .sprotty > .sprotty-root > svg.sprotty-graph": {
            "height": "unset!important",
        },
        " .dashed.elkedge > path ": {
            "stroke-dasharray": "3 3",
        },
        " text.elklabel.node_type_label": {
            "font-style": "italic",
        },
    }

    def add_relationship(
        self,
        source: Union[Node, Port],
        target: Union[Node, Port],
        cls: Type[Relationship] = Relationship,
        data: dict = None,
    ) -> Relationship:
        data = data or {}
        relationship = cls(source=source, target=target, data=data)
        self.edges.append(relationship)
        return relationship
