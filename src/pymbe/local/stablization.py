from ..label import *
from pymbe.interpretation.calc_dependencies import generate_execution_order, generate_parameter_signature_map

def build_stable_id_lookups(all_elements: dict, lpg: SysML2LabeledPropertyGraph) -> tuple:
    """
    Builds forward and reverse lookups for stable names
    :return: dicts of stable signature -> unique identifier
    """

    exec_order = generate_execution_order(lpg)
    sig_map = generate_parameter_signature_map(all_elements, exec_order)

    id_to_qualified_name = {}
    qualified_name_to_id = {}

    for ele_id, node in dict(lpg.nodes).items():
        qualified_label = get_qualified_label(node, all_elements, sig_map, True)
        id_to_qualified_name.update({ele_id: qualified_label})
        if qualified_label in qualified_name_to_id:
            print(f"Duplicate name found for {qualified_label}")

        qualified_name_to_id.update({qualified_label: ele_id})

    return (id_to_qualified_name, qualified_name_to_id)