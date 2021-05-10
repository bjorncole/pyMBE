import networkx as nx
from ..interpretation.results import pprint_double_id_list
from ..label import get_label_for_id
from ..graph.lpg import SysML2LabeledPropertyGraph

def build_dependency_graph(
    lpg: SysML2LabeledPropertyGraph,
    instance_dict: dict
) -> nx.MultiDiGraph:
    """
    Generate a dependency graph between specific sequences in the m0 interpretation
    :return:
    """

    all_elements = lpg.nodes
    eeg = lpg.get_projection("Expression Evaluation Graph")

    dependency_graph = nx.MultiDiGraph()

    sorted_feature_groups = []
    for comp in nx.connected_components(eeg.to_undirected()):
        connected_sub = nx.subgraph(eeg, list(comp))
        ordered_sub = list(nx.topological_sort(connected_sub))
        #leaves = [node for node in connected_sub.nodes if connected_sub.out_degree(node) == 0]
        #roots = [node for node in connected_sub.nodes if connected_sub.in_degree(node) == 0]
        #for leaf in leaves:
        #    for root in roots:
        #        try:
            # FIXME: This seems to be missing some connections in the graph
            # FIXME: Remember - don't need to sort!
            # leaf_path = nx.shortest_path(connected_sub, root, leaf)
        has_expression = any([
            "Expression" in all_elements[step]["@type"]
            or "Literal" in all_elements[step]["@type"]
            or "AttributeUsage" == all_elements[step]["@type"]
            for step in ordered_sub #leaf_path
        ])
        if has_expression:
            #leaf_path.reverse()
            sorted_feature_groups.append(ordered_sub)
    #        except:
    #            pass

    for sorted in sorted_feature_groups:
        for index, item in enumerate(sorted):
            sorted_preds = eeg.predecessors(item)
            for pred in sorted_preds:
                source_instances = instance_dict[pred]
                target_instances = instance_dict[item]
                #print("Pred = " + get_label_for_id(pred, all_elements))
                #print(source_instances)
                #print("Item = " + get_label_for_id(item, all_elements))
                #print(target_instances)

            # ignore first element to build edges
            #if index > 0:
            #    source_instances = instance_dict[sorted[index - 1]]
            #    target_instances = instance_dict[item]

                for jndx, source_inst in enumerate(source_instances):
                    tuple_key_source = (pred, jndx, len(source_inst))
                    tuple_key_target = (item, jndx, len(target_instances[jndx]))
                    dependency_graph.add_edge(tuple_key_source, tuple_key_target)

    return dependency_graph