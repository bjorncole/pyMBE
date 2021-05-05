import networkx as nx
from ..interpretation.results import pprint_double_id_list
from ..graph.lpg import SysML2LabeledPropertyGraph

def build_dependency_graph(
    lpg: SysML2LabeledPropertyGraph,
    instance_dict: dict
) -> nx.DiGraph:
    """
    Generate a dependency graph between specific sequences in the m0 interpretation
    :return:
    """
    all_elements = lpg.nodes
    eeg = lpg.get_projection("Expression Evaluation Graph")

    sorted_feature_groups = []
    for comp in nx.connected_components(eeg.to_undirected()):
        connected_sub = nx.subgraph(eeg, list(comp))
        leaves = [node for node in connected_sub.nodes if connected_sub.out_degree(node) == 0]
        roots = [node for node in connected_sub.nodes if connected_sub.in_degree(node) == 0]
        for leaf in leaves:
            for root in roots:
                try:
                    leaf_path = nx.shortest_path(connected_sub, root, leaf)
                    has_expression = any([
                        "Expression" in all_elements[step]["@type"]
                        or "Literal" in all_elements[step]["@type"]
                        or "AttributeUsage" == all_elements[step]["@type"]
                        for step in leaf_path
                    ])
                    if has_expression:
                        #leaf_path.reverse()
                        sorted_feature_groups.append(leaf_path)
                except:
                    pass

    print(pprint_double_id_list(sorted_feature_groups, all_elements))

    return None