# Module for computing useful labels and signatures for SysML v2 elements


def get_m1_signature_label(element: dict, all_elements: dict) -> str:
    element_name = element.get("name")
    element_metatype = element.get("@type")

    # Get the element type(s)
    element_types: list = element.get("type") or []
    if isinstance(element_types, dict):
        element_types = [element_types]
    element_types = [
        all_elements[element_type["@id"]].get("name")
        for element_type in element_types
        if element_type and "@id" in element_type
    ]
    element_types = [
        str(element_type)
        for element_type in element_types
        if element_type
    ]

    if element_name:
        if element_types:
            element_name += f": {element_types[0]}"
        return element_name
    elif element_metatype == "FeatureReferenceExpression":
        referent = all_elements[element["referent"]["@id"]]
        referent_name = (
            referent["name"] or
            referent["qualifiedName"].split("::")[-2]
        )
        return f"FRE.{referent_name}"
    elif element_metatype in (
        "Expression",
        "OperatorExpression",
        "InvocationExpression",
    ):
        return _get_m1_signature_label_for_expressions(
            element=element,
            all_elements=all_elements,
            element_metatype=element_metatype,
            element_types=element_types,
        )
    elif "@id" in element:
        return f"""{element["@id"]} «{element_metatype}»"""
    else:
        return "blank"


def _get_m1_signature_label_for_expressions(
    element: dict,
    all_elements: dict,
    element_metatype: str,
    element_types: list,
) -> str:
    input_ids = [
        expression_input["@id"]
        for expression_input in element["input"]
    ]
    input_names = [
        all_elements[input_id]["name"]
        for input_id in input_ids
    ]
    result_id = element["result"]["@id"]
    result_name = all_elements[result_id]["name"]
    prefix = ""
    if element_metatype == "Expression":
        parameter_members = [result_id] + input_ids
        # Scan memberships to find non-parameter members
        non_parameter_members = [
            get_m1_signature_label(
                element=all_elements[owned_member["@id"]],
                all_elements=all_elements,
            )
            for owned_member in element["ownedMember"]
            if owned_member["@id"] not in parameter_members
        ]
        prefix = non_parameter_members[0] if non_parameter_members else ""
    elif element_metatype == "OperatorExpression":
        prefix = element["operator"]
    elif element_metatype == "InvocationExpression":
        prefix = element_types[0] if element_types else ""
    return f"""{prefix}({", ".join(input_names)}) => {result_name}"""
