import ipytree as ipyt
import ipywidgets as ipyw
import traitlets as trt
import typing as ty

from .core import BaseWidget


ICONS_FOR_TYPES = {
    "Package": "archive",  # "cube" or "box" or "box-open"
    "ItemDefinition": "file-invoice",  # "info"
    "PartDefinition": "file-powerpoint",
    "StateDefinition": "file-contract",
    "ActionUsage": "copy",
    "AttributeUsage": "copy",  # "underline"
    "PartUsage": "copy",
    "ReferenceUsage": "code-branch",
    "MultiplicityRange": "ellipsis-h",  # "star-of-life" or "share-alt-square"
    "LiteralInteger": "quote-right",
    "LiteralReal": "quote-right",
    "Feature": "terminal",  # "pencil-alt"
    "Expression": "code",
    "Function": "square-root-alt",
    "OperatorExpression": "broom",  # "hashtag"
    "InvocationExpression": "comment-alt",
    "Succession": "long-arrow-alt-right",
}

DEFAULT_ICON = "genderless"


class Element(ipyt.Node):
    """A project element node compatible with ipytree."""

    _identifier: str = trt.Unicode()
    _owner: str = trt.Unicode("self", allow_none=True)
    _type: str = trt.Unicode()
    _data: dict = trt.Dict()


@ipyw.register
class ContainmentTree(ipyt.Tree, BaseWidget):
    """A widget to explore the structure and data in a project."""

    description = trt.Unicode("Containment Tree").tag(sync=True)
    nodes_by_id: ty.Dict[str, Element] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(Element),
        kw={},
    )

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        layout.overflow_y = "auto"
        layout.width = "auto"
        return layout

    @trt.observe("elements_by_id")
    def update(self, *_, elements: dict = None):
        elements = elements or self.elements_by_id
        nodes = {
            element_id: self._make_node(element=element)
            for element_id, element in elements.items()
        }
        for node in nodes.values():
            if node._owner in nodes:
                nodes[node._owner].add_node(node)

        # Filter nodes to those that have subnodes or a proper name
        nodes = {
            id_: node
            for id_, node in nodes.items()
            if node.nodes
            or node._data.get("name", None)
        }
        # Sort the child nodes
        for node in nodes.values():
            node.nodes = self.sort_nodes(node.nodes)

        with self.hold_trait_notifications():
            self.selected = []
            self.nodes_by_id = nodes

    @trt.observe("selected_nodes")
    def _update_selected(self, *_):
        self.selected = [
            node._identifier
            for node in self.selected_nodes
        ]

    @trt.observe("selected")
    def _update_selected_elements(self, *_):
        if not self.selected:
            self.deselect_nodes()
            return
        with self.hold_trait_notifications():
            self.select_nodes(*self.selected)
            nodes_to_deselect = [
                node
                for node in self.selected_nodes
                if node._identifier not in self.selected
            ]
            if nodes_to_deselect:
                self.deselect_nodes(*nodes_to_deselect)

    @trt.observe("nodes_by_id")
    def _update_tree(self, *_):
        # find the root nodes and sort them
        roots = self.sort_nodes([
            node for node in self.nodes_by_id.values()
            if node._owner is None
        ])

        # update the tree
        self._clear_tree()
        for root in roots:
            self.add_node(root)

    def select_nodes(self, *nodes: str):
        """Select a list of nodes"""
        with self.hold_trait_notifications():
            for node_id in nodes:
                node = self.nodes_by_id.get(node_id, None)
                if node is None:
                    continue
                node.selected = True

    def deselect_nodes(self, *nodes: str):
        """Deselect a node, or deselect all if none is specified."""
        nodes = nodes or [
            node
            for node_id, node in self.nodes_by_id.items()
            if node.selected
        ]
        with self.hold_trait_notifications():
            for node in nodes:
                node.selected = False

    def _clear_tree(self):
        for node in self.nodes:
            self.remove_node(node)
            del node

    @staticmethod
    def _make_node(element):
        element_id = element["@id"]

        owner = (
            element.get("owner", None)
            or element.get("owningRelatedElement", None)
            or {}
        ).get("@id", None)

        return Element(
            icon=ICONS_FOR_TYPES.get(element["@type"], DEFAULT_ICON),
            name=(
                element["name"]
                or f"""«{element["@type"]}: {element_id}»"""
            ),
            _data=element,
            _identifier=element_id,
            _owner=owner,
            _type=element["@type"],
        )

    @staticmethod
    def sort_nodes(nodes: (list, tuple, set)) -> tuple:
        # Sort nodes with number of subnodes first and then by name
        return tuple(sorted(
            nodes,
            key=lambda n: (-len(n.nodes), n.name),
        ))
