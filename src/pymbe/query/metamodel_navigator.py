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
