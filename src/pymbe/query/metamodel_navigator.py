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


def map_inputs_to_results(lpg: SysML2LabeledPropertyGraph) -> list:
    eeg = lpg.get_projection("Expression Evaluation Graph")

    edge_dict = {
        edge["@id"]: edge
        for edge in lpg.edges.values()
    }
    return_parameter_memberships = [
        lpg.edges[(source, target, kind)]
        for source, target, kind in lpg.edges
        if kind == "ReturnParameterMembership"
    ]

    implied_edges = []
    for membership in return_parameter_memberships:
        for result_feeder_id in eeg.predecessors(membership["memberElement"]["@id"]):
            result_feeder = lpg.nodes[result_feeder_id]
            rf_metatype = result_feeder["@type"]
            # we only want Expressions that have at least one input parameter
            if "Expression" not in rf_metatype or rf_metatype in ["FeatureReferenceExpression"]:
                continue

            expr_results = []
            expr_members, para_members, result_members = [], [], []
            # assume that the members of an expression that are themselves
            # members are referenced in the same order as parameters - results
            # of an expression should feed into the input parameter owned by
            # its owner

            owned_memberships = result_feeder["ownedMembership"]
            for om_id in owned_memberships:
                relationship = edge_dict[om_id["@id"]]
                relationship_metatype = relationship["@type"]
                edge_member_id = relationship["memberElement"]["@id"]
                if "Parameter" in relationship_metatype:
                    if "ReturnParameter" in relationship_metatype:
                        result_members.append(edge_member_id)
                    else:
                        para_members.append(edge_member_id)
                elif any(
                    kind in relationship_metatype
                    for kind in ("Membership", "Result")
                ):
                    expr_members.append(edge_member_id)
                    edge_member_result_id = lpg.nodes[edge_member_id].get("result", {}).get("@id")
                    if edge_member_result_id:
                        expr_results.append(edge_member_result_id)

            implied_edges += [
                (expr_results[index], para_members[index], "ImpliedParameterFeedforward")
                for index, expr in enumerate(expr_members)
                if index < len(expr_results) and index < len(para_members)
            ]

    return implied_edges
