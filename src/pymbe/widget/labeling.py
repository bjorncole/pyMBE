# Module for computing useful labels and signatures for SysML v2 elements


def get_m1_signature_label(element: dict, all_elements: dict) -> str:
    name = element.get("name")
    metatype = element.get("@type")

    # Get the element type(s)
    types: list = element.get("type") or []
    if isinstance(types, dict):
        types = [types]
    type_names = [
        all_elements[type_["@id"]].get("name")
        for type_ in types
        if type_ and "@id" in type_
    ]
    type_names = [
        str(type_name)
        for type_name in type_names
        if type_name
    ]

    if name:
        if type_names:
            # TODO: look into using other types (if there are any)
            name += f": {type_names[0]}"
        return name
    elif metatype.endswith("Expression"):
        return _get_m1_signature_label_for_expressions(
            element=element,
            all_elements=all_elements,
            metatype=metatype,
            type_names=type_names,
        )
    elif "@id" in element:
        return f"""{element["@id"]} «{metatype}»"""
    else:
        return "blank"


def _get_m1_signature_label_for_expressions(
    element: dict,
    all_elements: dict,
    metatype: str,
    type_names: list,
) -> str:
    if metatype not in (
        "Expression",
        "FeatureReferenceExpression",
        "InvocationExpression",
        "OperatorExpression",
    ):
        raise NotImplementedError(
            f"Cannot create M1 signature for: {metatype}"
        )

    if metatype == "FeatureReferenceExpression":
        referent_id = (element["referent"] or {}).get("@id")
        referent = all_elements.get(referent_id)
        if referent:
            referent_name = referent["name"]
            name_chain = referent["qualifiedName"].split("::")
            index = 0
            while not referent_name and index < len(name_chain):
                index += 1
                referent_name = name_chain[-index]
                if referent_name.lower() == "null":
                    referent_name = None
        else:
            referent_name = "UNNAMED"
        return f"FRE.{referent_name}"

    prefix = ""
    input_ids = [
        expression_input["@id"]
        for expression_input in element["input"]
    ]
    input_names = [
        all_elements[input_id]["name"]
        for input_id in input_ids
    ]
    result_id = (element["result"] or {}).get("@id")
    result_name = all_elements.get(result_id, {}).get("name")

    if metatype == "Expression":
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
    elif metatype == "OperatorExpression":
        prefix = element["operator"]
    elif metatype == "InvocationExpression":
        prefix = type_names[0] if type_names else ""
    return f"""{prefix} ({", ".join(input_names)}) => {result_name}"""
