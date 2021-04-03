import networkx as nx

from .graph import SysML2LabeledPropertyGraph


def retrieve_element(elements: dict, element: (dict, str), strict: bool = True) -> dict:
    input_element = element
    if isinstance(element, str):
        element = elements.get(element, None)
    elif not isinstance(element, dict):
        raise ValueError(f"Failed to process element: '{input_element}'")
    if strict and element is None:
        raise ValueError(f"Failed to process element: '{input_element}'")
    return element


def get_metaclass(elements: dict, element: (dict, str)) -> str:
    element = retrieve_element(elements, element)
    return element.get("@type", None)


def get_feature_upper_multiplicity(elements: dict, feature: (dict, str)) -> int:
    feature = retrieve_element(elements, feature)

    multiplicity = elements.get((feature.get("multiplicity", None) or {}).get("@id", None), None)
    if multiplicity is None:
        return None
    upper_bound = elements.get((multiplicity.get("upperBound", {}) or {}).get("@id", {}), None)
    if upper_bound is None:
        return None
    return upper_bound.get("value", None)


def make_banded_featuring_graph(lpg: SysML2LabeledPropertyGraph) -> nx.DiGraph:
    return lpg.filter(
        edge_types=(
            "FeatureMembership",
            "FeatureTyping",
            "Redefinition",
            "Superclassing",
        ),
        reverse_edge_types=(
            "FeatureMembership",
            "FeatureTyping",
        )
    )

