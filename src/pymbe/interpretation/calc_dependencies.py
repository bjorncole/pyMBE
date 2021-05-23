import networkx as nx
from ..interpretation.results import pprint_double_id_list
from ..label import get_label_for_id
from ..graph.lpg import SysML2LabeledPropertyGraph

def generate_execution_order(
    lpg: SysML2LabeledPropertyGraph,
    instance_dict: dict
) -> list:
    """
    Generate a dependency graph between specific sequences in the m0 interpretation
    :return:
    """

    all_elements = lpg.nodes
    eig = lpg.get_projection("Expression Inferred Graph")

    execution_pairs = []
    execution_contexts = {}

    # use the BFS rollup method from the playbook phase 2

    roots = [node for node in eig.nodes if eig.in_degree(node) == 0]

    for root in roots:
        context = all_elements[root]['featuringType'][0]['@id']
        execution_contexts.update({context: []})

        bfs_dict = dict(nx.bfs_successors(eig, root))
        bfs_list = list(bfs_dict.keys())
        bfs_list.reverse()

        for node in bfs_list:
            bfs_check = []
            for node_child in bfs_dict[node]:
                kind = ''

                if all_elements[node_child]['@type'] == 'Feature' and all_elements[node]['@type'] == 'Feature':
                    kind = 'Assignment'
                elif all_elements[node_child]['@type'] == 'AttributeUsage' and all_elements[node]['@type'] == 'AttributeUsage':
                    relevant_edge_types = [edg[2] for edg in eig.edges if edg[0] == node and edg[1] == node_child]
                    if "Redefinition^-1" in relevant_edge_types:
                        kind = 'Redefinition'
                    else:
                        kind = 'Assignment'
                elif all_elements[node_child]['@type'] == 'Feature' and all_elements[node]['@type'] == 'AttributeUsage':
                    kind = 'ValueBinding'
                elif (node_child, node, 'ReturnParameterMembership') in lpg.edges_by_type['ReturnParameterMembership']:
                    kind = 'Output'
                elif (node, node_child, 'ParameterMembership') in lpg.edges_by_type['ParameterMembership']:
                    kind = 'Input'

                execution_pairs.append([node_child, node, kind])
                bfs_check.append([node_child, node])

                execution_contexts[context].append(node_child)

            # need to account for fact that BFS only visit nodes once ... need to fill in additional edges
            for pred in eig.successors(node):
                if [pred, node] in bfs_check:
                    pass
                    #print("Matched edge from BFS")
                else:
                    print("Need to add edge for " + str([pred, node]))
                    kind = ''

                    if all_elements[node_child]['@type'] == 'Feature' and all_elements[node]['@type'] == 'Feature':
                        kind = 'Assignment'
                    elif all_elements[node_child]['@type'] == 'AttributeUsage' and all_elements[node][
                        '@type'] == 'AttributeUsage':
                        kind = 'Assignment'
                    elif all_elements[node_child]['@type'] == 'Feature' and all_elements[node][
                        '@type'] == 'AttributeUsage':
                        kind = 'ValueBinding'
                    elif (node_child, node, 'ReturnParameterMembership') in lpg.edges_by_type[
                        'ReturnParameterMembership']:
                        kind = 'Output'
                    elif (node, node_child, 'ParameterMembership') in lpg.edges_by_type['ParameterMembership']:
                        kind = 'Input'

                    execution_pairs.append([pred, node, kind])

    return execution_pairs