from ..graph import SysML2LabeledPropertyGraph
from ..interpretation.calc_dependencies import (
    generate_execution_order,
    generate_parameter_signature_map,
)
from ..label import get_qualified_label


def build_stable_id_lookups(lpg: SysML2LabeledPropertyGraph) -> tuple:
    """Builds forward and reverse lookups for stable names :return: dicts of
    stable signature -> unique identifier."""
    exec_order = generate_execution_order(lpg)
    sig_map = generate_parameter_signature_map(lpg.model, exec_order)

    id_to_qualified_name, qualified_name_to_id = {}, {}
    for element_id in lpg.nodes:
        element = lpg.model.elements[element_id]
        qualified_label = get_qualified_label(element, sig_map, True)
        id_to_qualified_name.update({element_id: qualified_label})
        if qualified_label in qualified_name_to_id:
            print(f"Duplicate name found for: '{qualified_label}'")
        qualified_name_to_id.update({qualified_label: element_id})

    return (id_to_qualified_name, qualified_name_to_id)
