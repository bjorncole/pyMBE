# Module for computing useful labels and signatures for SysML v2 elements
from .graph.lpg import SysML2LabeledPropertyGraph

def get_label(
    element: dict,
    all_elements: dict
) -> str:
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
    value = element.get("value")
    if name:
        if type_names:
            # TODO: look into using other types (if there are any)
            name += f": {type_names[0]}"
        return name
    elif value and metatype.startswith("Literal"):
        metatype = type_names[0] if type_names else metatype.replace("Literal", "Occurred Literal")
        return f"{value} «{metatype}»"
    elif metatype == "MultiplicityRange":
        return get_label_for_multiplicity(
            multiplicity=element,
            all_elements=all_elements
        )
    elif metatype.endswith("Expression"):
        return get_label_for_expression(
            expression=element,
            all_elements=all_elements,
            type_names=type_names
        )
    elif "@id" in element:
        return f"""{element["@id"]} «{metatype}»"""
    else:
        return "blank"


def get_label_for_id(
    element_id: str,
    all_elements: dict
) -> str:
    return get_label(all_elements[element_id], all_elements)


def get_label_for_expression(
    expression: dict,
    all_elements: dict,
    type_names: list
) -> str:
    metatype = expression["@type"]
    if metatype not in (
        "Expression",
        "FeatureReferenceExpression",
        "InvocationExpression",
        "OperatorExpression",
        "PathStepExpression"
    ):
        raise NotImplementedError(
            f"Cannot create M1 signature for: {metatype}"
        )

    if metatype == "FeatureReferenceExpression":
        referent_id = (expression["referent"] or {}).get("@id")
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
        for expression_input in expression["input"]
    ]
    input_names = [
        get_label_for_input_parameter(all_elements[input_id], all_elements)
        for input_id in input_ids
    ]
    result_id = (expression["result"] or {}).get("@id")
    result_name = all_elements.get(result_id, {}).get("name")

    if metatype == "Expression":
        parameter_members = [result_id] + input_ids
        # Scan memberships to find non-parameter members
        non_parameter_members = [
            get_label(
                element=all_elements[owned_member["@id"]],
                all_elements=all_elements
            )
            for owned_member in expression["ownedMember"]
            if owned_member["@id"] not in parameter_members
        ]
        prefix = non_parameter_members[0] if non_parameter_members else ""
    elif metatype == "OperatorExpression":
        prefix = expression["operator"]
    elif metatype == "InvocationExpression":
        prefix = type_names[0] if type_names else ""
    elif metatype == "PathStepExpression":
        path_step_names = []
        for owned_fm_id in expression["ownedFeatureMembership"]:
            owned_fm = all_elements[owned_fm_id["@id"]]
            if owned_fm["@type"] == "FeatureMembership":
                member = all_elements[owned_fm["memberElement"]["@id"]]
                # expect FRE here
                if "referent" in member:
                    refered = all_elements[member["referent"]["@id"]]
                    path_step_names.append(refered.get("name") or refered["@id"])

        prefix = ".".join(path_step_names)
    return f"""{prefix} ({", ".join(input_names)}) => {result_name}"""


def get_label_for_input_parameter(
    parameter: dict,
    all_elements: dict
) -> str:

    return f"""{parameter["name"]}"""

def get_label_for_multiplicity(
    multiplicity: dict,
    all_elements: dict
) -> str:
    limits = {
        "lower": "0",
        "upper": "*",
    }
    values = {}
    for limit, default in limits.items():
        literal_id = (multiplicity[f"{limit}Bound"] or {}).get("@id")
        if literal_id is None:
            values[limit] = default
            continue
        values[limit] = (
            all_elements.get(literal_id) or {}
        ).get("value", default)
    return f"""{values["lower"]}..{values["upper"]}"""


def get_qualified_label(element: dict, all_elements: dict, parameter_name_map: dict, start: bool) -> str:

    earlier_name = "Model"

    if "owner" in element:
        if element["owner"] is not None:
            element_owner = all_elements[element["owner"]["@id"]]
            earlier_name = get_qualified_label(element_owner, all_elements, parameter_name_map, False)
    else:

        name = element["name"]
        return f"{name}"

    printed_name = ""
    if element["@id"] in parameter_name_map:
        printed_name = parameter_name_map[element["@id"]]
    else:
        printed_name = get_label(element, all_elements)

    tail = ""
    if start:
        tail = " <<" + element["@type"] + ">>"
    earlier_name = f"{earlier_name}::{printed_name}{tail}"

    return earlier_name
