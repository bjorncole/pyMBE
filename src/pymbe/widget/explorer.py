from copy import deepcopy

from IPython.display import JSON, display

import ipytree as ipyt
import ipywidgets as ipyw
import traitlets as trt


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

    _identifier = trt.Unicode()
    _owner = trt.Unicode("self", allow_none=True)
    _type = trt.Unicode()
    _data = trt.Dict()


class ProjectExplorer(ipyw.HBox):
    """A widget to explore the structure and data in a project."""

    FILTER_KEYS = ("@context",)

    data_display: ipyw.Output = trt.Instance(ipyw.Output, args=())
    elements_by_id: dict = trt.Dict()
    nodes: dict = trt.Dict(kw={})
    selected: tuple = trt.Tuple(trt.Unicode())
    tree: ipyt.Tree = trt.Instance(ipyt.Tree)

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [
            self.tree,
            self.data_display,
        ]

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        # layout.grid_template_columns = "repeat(2, auto)"
        layout.height = "100%"
        layout.width = "auto"
        return layout

    @trt.default("tree")
    def _make_tree(self) -> ipyt.Tree:
        tree = ipyt.Tree(
            multiple_selection=True,
            layout=dict(width="45%"),
        )
        tree.observe(self._update_selected, "selected_nodes")
        return tree

    @trt.default("data_display")
    def _make_data_display(self) -> ipyw.Output:
        return ipyw.Output(layout=dict(width="45%"))

    @trt.observe("tree")
    def _update_selected_node_observer(self, change: trt.Bunch = None):
        change = change or {}
        if change.get("old"):
            change.old.unobserve(self._update_selected)
            del change.old
        self.tree.observe(self._update_selected, "selected_nodes")

    @trt.observe("selected")
    def _update_details(self, *_):
        self.data_display.outputs = self._make_JSON_output()

    @trt.observe("elements_by_id")
    def _update_elements(self, *_):
        self.update(elements=self.elements_by_id)
        self.data_display.outputs = []

    def _update_selected(self, *_):
        if not self.tree.selected_nodes:
            self.selected = []
            return
        self.selected = [
            node._identifier
            for node in self.tree.selected_nodes
        ]

    def get_element_data(self, element_id: str) -> dict:
        return {
            key: value
            for key, value in self.elements_by_id.get(element_id, {}).items()
            if key not in self.FILTER_KEYS
        }

    def _clear_tree(self):
        tree = self.tree
        for node in tree.nodes:
            tree.remove_node(node)

    def _make_node(self, element):
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
            _identifier=element_id,
            _type=element["@type"],
            _owner=owner,
            _data=element,
        )

    def update(self, elements: dict):
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
        self.nodes = nodes

    @staticmethod
    def sort_nodes(nodes: (list, tuple, set)) -> tuple:
        # Sort nodes with number of subnodes first and then by name
        return tuple(sorted(
            nodes,
            key=lambda n: (-len(n.nodes), n.name),
        ))

    @trt.observe("nodes")
    def _update_tree(self, *_):

        # find the root nodes and sort them
        roots = self.sort_nodes([
            node for node in self.nodes.values()
            if node._owner is None
        ])

        # update the tree
        self._clear_tree()
        tree = self.tree
        for root in roots:
            tree.add_node(root)

    def _make_JSON_output(self) -> list:
        return [
            {
                "output_type": "display_data",
                "data": {
                    "text/plain": f"JSON Display for {id_}",
                    "application/json": self.elements_by_id.get(id_, {}),
                },
                "metadata": {
                    "application/json": {
                        "expanded": False,
                        "root": id_,
                    },
                },
            }
            for id_ in self.selected
        ]
