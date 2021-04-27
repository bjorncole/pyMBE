# a collection of convenience methods to navigate the metamodel when inspecting user models

from ..graph.lpg import SysML2LabeledPropertyGraph
from ..label import get_label


def feature_multiplicity(
    feature: dict,
    all_elements: dict,
    bound: str,
):
    if bound not in ("upper", "lower"):
        raise ValueError(f"'bound' must be 'upper' or 'lower', not '{bound}'")

    multiplicity_id = (feature.get("multiplicity") or {}).get("@id")
    if multiplicity_id:
        bound += "Bound"
        multiplicity = all_elements[multiplicity_id]
        if "@id" in multiplicity[bound]:
            return all_elements[multiplicity[bound]["@id"]]["value"]

    return 1


def map_inputs_to_results(
    lpg: SysML2LabeledPropertyGraph
) -> list:
    implied_edges = []

    eeg = lpg.get_projection("Expression Evaluation Graph")

    edge_dict = {}
    for edge in lpg.edges.values():
        edge_dict.update({edge['@id']: edge})

    rpms = [lpg.edges[edg] for edg in list(lpg.edges.keys()) if edg[2] == 'ReturnParameterMembership']

    for rpm in rpms:
        for result_feeder in eeg.predecessors(rpm['memberElement']['@id']):
            # I think what we really want is Expressions that have at least one input parameter
            if 'Expression' in lpg.nodes[result_feeder]['@type'] and lpg.nodes[result_feeder][
                    '@type'] != 'FeatureReferenceExpression':
                expr_members = []
                para_members = []
                expr_results = []
                result_members = []
                # assume that the members of an expression that are themselves members are referenced in the same
                # order as parameters - results of an expression should feed into the input parameter owned by its
                # owner

                ownedMemberships = lpg.nodes[result_feeder]['ownedMembership']
                for om in ownedMemberships:
                    if 'Parameter' in edge_dict[om['@id']]['@type'] and edge_dict[om['@id']]['@type']:
                        if 'ReturnParameter' in edge_dict[om['@id']]['@type']:
                            result_members.append(edge_dict[om['@id']]['memberElement']['@id'])
                        else:
                            para_members.append(edge_dict[om['@id']]['memberElement']['@id'])
                    elif 'Membership' in edge_dict[om['@id']]['@type'] or 'Result' in edge_dict[om['@id']]['@type']:
                        # print(edge_dict[om['@id']])
                        edge_member = edge_dict[om['@id']]['memberElement']['@id']
                        expr_members.append(edge_dict[om['@id']]['memberElement']['@id'])
                        if 'result' in lpg.nodes[edge_member]:
                            expr_result = lpg.nodes[edge_member]['result']['@id']
                            expr_results.append(expr_result)
                edge_stack = []
                for indx, expr in enumerate(expr_members):
                    if indx < len(expr_results) and indx < len(para_members):
                        edge_stack.append(
                            get_label(lpg.nodes[expr], lpg.nodes) + ' --[' +
                            lpg.nodes[expr_results[indx]]['@id'] + ']--> ' +
                            get_label(lpg.nodes[para_members[indx]], lpg.nodes)
                        )

                        implied_edges.append((expr_results[indx], para_members[indx], "ImpliedParameterFeedforward"))

    return implied_edges