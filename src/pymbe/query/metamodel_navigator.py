# a collection of convenience methods to navigate the metamodel when inspecting user models

from ..graph.lpg import SysML2LabeledPropertyGraph


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
