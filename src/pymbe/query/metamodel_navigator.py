# a collection of convenience methods to navigate the metamodel when inspecting user models
from ..model import Element


def feature_multiplicity(feature: Element, bound: str) -> int:
    if bound not in ("upper", "lower"):
        raise ValueError(f"'bound' must be 'upper' or 'lower', not '{bound}'")
    multiplicity = feature.multiplicity
    if multiplicity:
        value = multiplicity[f"{bound}Bound"]
        if bound == "lower" and value is None:
            return multiplicity.upperBound.value
        if value is not None:
            return value.value
    return 1


def safe_feature_data(feature: Element, key: str) -> Element:
    if key not in feature._data:
        raise ValueError("Tried to get the '{key}' on an element without it!")
    values = feature._data[key]
    num_types = len(values)
    if num_types == 0:
        return None
    if num_types == 1:
        return feature._model.elements[values[0]["@id"]]

    raise NotImplementedError(f"No logic for multiple {key}!")
