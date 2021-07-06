# Module for computing useful labels and signatures for SysML v2 elements
from .model import Element, Model


# TODO: Refactor this whole thing and integrate it better with the new Model approach


def get_label(element: Element) -> str:
    metatype = element._metatype
    model = element._model
    data = element._data
    name = data.get("name")

    # Get the element type(s)
    types: list = data.get("type") or []
    if isinstance(types, dict):
        types = [types]
    type_names = [
        model.elements[type_["@id"]]._data.get("name")
        for type_ in types
    ]
    type_names = [
        str(type_name)
        for type_name in type_names
        if type_name
    ]
    value = element._data.get("value")
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
            model=model,
        )
    elif metatype.endswith("Expression"):
        return get_label_for_expression(
            expression=element,
            type_names=type_names,
        )
    elif "@id" in data:
        return f"""{data["@id"]} «{metatype}»"""
    else:
        return "blank"


def get_label_for_id(element_id: str, model: Model) -> str:
    return get_label(model.elements[element_id])


def get_label_for_expression(
    expression: Element,
    type_names: list,
) -> str:
    metatype = expression._metatype
    all_elements = expression._model.elements
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
        try:
            referent = expression.referent
            referent_name = referent.name
            name_chain = referent.qualifiedName.split("::")
            index = 0
            while not referent_name and index < len(name_chain):
                index += 1
                referent_name = name_chain[-index]
                if referent_name.lower() == "null":
                    referent_name = None
        except AttributeError:
            referent_name = "UNNAMED"
        return f"FRE.{referent_name}"

    prefix = ""
    inputs = expression.input
    if isinstance(inputs, Element):
        inputs = [inputs]
    input_names = [an_input.name for an_input in inputs]
    try:
        result: Element = expression.result
    except AttributeError:
        result = None

    if result and metatype == "Expression":
        parameter_members = [result] + inputs
        # Scan memberships to find non-parameter members
        non_parameter_members = [
            get_label(element=owned_member)
            for owned_member in expression.ownedMember
            if owned_member not in parameter_members
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
    return f"""{prefix} ({", ".join(input_names)}) => {result.name}"""


def get_label_for_multiplicity(
    multiplicity: dict,
    all_elements: dict,
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


def get_qualified_label(element: dict, all_elements: dict) -> str:

    earlier_name = ""

    try:
        if "owner" in element:
            if element["owner"] is not None:
                element_owner = all_elements[element["owner"]["@id"]]
                earlier_name = get_qualified_label(element_owner, all_elements)
        else:
            return element["name"]

        earlier_name = f"{earlier_name}::{get_label(element, all_elements)}"
    except TypeError:
        print(all_elements)

    return earlier_name
