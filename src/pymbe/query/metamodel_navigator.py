# a collection of convenience methods to navigate the metamodel when inspecting user models
from pymbe.graph import SysML2LabeledPropertyGraph


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
        # when a specific multiplicity is specified, lower is None, upper is the number
        if bound == "lowerBound" and multiplicity[bound] is None:
            return all_elements[multiplicity["upperBound"]["@id"]]["value"]
        elif "@id" in multiplicity[bound]:
            return all_elements[multiplicity[bound]["@id"]]["value"]

    return 1


def map_inputs_to_results(lpg: SysML2LabeledPropertyGraph) -> list:
    # TODO: Need a hack to feed result parameters into collection expressions

    eeg = lpg.get_projection("Expression Evaluation")

    edge_dict = {
        edge["@id"]: edge
        for edge in lpg.edges.values()
    }
    return_parameter_memberships = [
        lpg.edges[(source, target, kind)]
        for source, target, kind in lpg.edges
        if kind == "ReturnParameterMembership"
    ]

    feature_values = [
        (source, target, kind)
        for source, target, kind in lpg.edges
        if kind == "FeatureValue"
    ]

    implied_edges = []

    fres = [lpg.nodes[fre] for fre in eeg.nodes if lpg.nodes[fre]['@type'] == 'FeatureReferenceExpression']

    for fre in fres:
        implied_edges += [(fre['referent']['@id'], fre['@id'], "ImpliedParameterFeedforward")]

    for feature_val in feature_values:
        target_result_id = lpg.nodes[feature_val[1]]['result']['@id']
        implied_edges += [(target_result_id, feature_val[0], "ImpliedParameterFeedforward")]

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

            # NOTE: There is a special case for when there is a ResultExpressionMembership:
            # A ResultExpressionMembership is a FeatureMembership that indicates that the ownedResultExpression
            # provides the result values for the Function or Expression that owns it. The owning Function or
            # Expression must contain a BindingConnector between the result parameter of the ownedResultExpression
            # and the result parameter of the Function or Expression.
            rem_flag = False
            for om_id in owned_memberships:
                relationship = edge_dict[om_id["@id"]]
                relationship_metatype = relationship["@type"]
                edge_member_id = relationship["memberElement"]["@id"]
                if "Parameter" in relationship_metatype:
                    if "ReturnParameter" in relationship_metatype:
                        result_members.append(edge_member_id)
                    else:
                        para_members.append(edge_member_id)
                elif "Result" in relationship_metatype:
                    rem_owning_type = lpg.nodes[relationship["owningType"]["@id"]]
                    rem_owned_ele = lpg.nodes[relationship["ownedMemberElement"]["@id"]]
                    rem_flag = True
                elif "Membership" in relationship_metatype:
                    # print(edge_dict[om["@id"]])
                    edge_member = relationship["memberElement"]["@id"]
                    expr_members.append(edge_member)
                    if "result" in lpg.nodes[edge_member]:
                        expr_result = lpg.nodes[edge_member]["result"]["@id"]
                        expr_results.append(expr_result)

            # FIXME: This is a bit of a mess
            if rem_flag:
                rem_cheat_expr = rem_owned_ele["@id"]
                rem_cheat_result = rem_owned_ele["result"]["@id"]
                rem_cheat_para = rem_owning_type["result"]["@id"]

                expr_members = [rem_cheat_expr]
                expr_results = [rem_cheat_result]
                para_members = [rem_cheat_para]

            implied_edges += [
                (expr_results[index], para_members[index], "ImpliedParameterFeedforward")
                for index, expr in enumerate(expr_members)
                if index < len(expr_results) and index < len(para_members)
            ]

            # FIXME: Another hack to deal with collect inputs
            if rf_metatype == 'Expression':
                expr_owner = result_feeder['owner']['@id']
                expr_result_id = result_feeder['result']['@id']

                implied_edges+=[(expr_result_id, expr_owner, "ImpliedParameterFeedforward")]

    return implied_edges


def safe_get_type_by_id(
    lpg: SysML2LabeledPropertyGraph,
    feature_id: str
):
    feature = lpg.nodes[feature_id]
    if 'type' not in feature:
        raise ValueError("Tried to get the type on an element without a type!")

    no_types = len(feature['type'])
    if no_types == 0:
        return None
    elif no_types == 1:
        return lpg.nodes[feature['type'][0]['@id']]
    else:
        raise NotImplementedError("No logic for multiple types!")


def safe_get_featuring_type_by_id(
    lpg: SysML2LabeledPropertyGraph,
    feature_id: str
):
    feature = lpg.nodes[feature_id]
    if 'featuringType' not in feature:
        raise ValueError("Tried to get the type on an element without a featuring type!")

    no_types = len(feature['featuringType'])
    if no_types == 0:
        return None
    elif no_types == 1:
        return lpg.nodes[feature['featuringType'][0]['@id']]
    else:
        raise NotImplementedError("No logic for multiple types!")
