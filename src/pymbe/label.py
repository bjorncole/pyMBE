# TODO: Refactor this whole thing and integrate it better with the new Model approach
# Module for computing useful labels and signatures for SysML v2 elements
from warnings import warn

from .model import Element, Model

DEFAULT_MULTIPLICITY_LIMITS = dict(lower="0", upper="*")


def get_label(element: Element) -> str:
    metatype = element._metatype
    if metatype.endswith("Expression") :
        return f"{get_label_for_expression(element)} «{metatype}»"
    if metatype == "Invariant" and "throughResultExpressionMembership" in element._derived:
        return f"{get_label_for_expression(element.throughResultExpressionMembership[0])} «{metatype}»"
    model = element._model
    data = element._data
    name = data.get("name") or data.get("effectiveName") or data.get("declaredName")

    # Get the element type(s)
    types: list = data.get("type") or []
    if isinstance(types, dict):
        types = [types]
    try:
        type_names = [model.elements[type_["@id"]]._data.get("name") for type_ in types]
        type_names = [str(type_name) for type_name in type_names if type_name]
    except KeyError:
        type_names = ["Unresolved type"]
    value = element._data.get("value")
    
    if name:
        if type_names:
            # TODO: look into using other types (if there are any)
            name += f": {type_names[0]}"
        return f"{name} «{metatype}»"
    if metatype == "Feature" and "memberName" in element.owningRelationship._data and \
            element.owningRelationship._metatype in ("ParameterMembership", "ReturnParameterMembership"):
        direction = ''
        if "direction" in element._data:
            direction = element.direction + ' '
        para_string = element.owningRelationship._data["memberName"]
        return f"{direction}{para_string} «{metatype}»"

    if value and metatype.startswith("Literal"):
        metatype = type_names[0] if type_names else metatype.replace("Literal", "Occurred Literal")
        return f"{value} «{metatype}»"
    if metatype == "MultiplicityRange":
        return get_label_for_multiplicity(multiplicity=element)
    
    if "@id" in data:
        return f"""{data["@id"]} «{metatype}»"""

    return "blank"


def get_label_for_id(element_id: str, model: Model) -> str:
    return get_label(model.elements[element_id])


def get_label_for_expression(expression: Element) -> str:

    meta = expression._metatype

    expression_label = f"<<{meta} {expression._id}>>"

    if meta == "OperatorExpression":
        # case for OperatorExpression - recurse on the parameters

        expression_label = f" {expression.operator} ".join(
            map(get_label_for_expression, expression.throughParameterMembership)
        )

    # case for the Features under an expression
    elif meta == "Feature":
        expression_label = get_label_for_expression(expression.throughFeatureValue[0])

    elif meta == "FeatureReferenceExpression":
        # case for FeatureReferenceExpression - terminal case #1
        expression_label = expression.throughMembership[0].declaredName
    elif meta == "FeatureChainExpression":
        # first item will be FRE to another feature
        expression_label = (
            expression.throughParameterMembership[0]
            .throughFeatureValue[0]
            .throughMembership[0]
            .declaredName
        )
        # check if this is a two-item feature chain or n > 2
        if "throughMembership" in expression._derived:
        #if hasattr(expression, "throughMembership"):
            # this is the n = 2 case
            second_item = expression.throughMembership[0].declaredName
            expression_label += f".{second_item}"
        else:
            # this is the n > 2 case
            chains = expression.throughOwningMembership[0].throughFeatureChaining
            other_items = ".".join([chain.declaredName for chain in chains])
            expression_label += f".{other_items}"

    # covers Literal expression cases
    elif "value" in expression._data:
    #elif hasattr(expression, "value"):
        expression_label = str(expression.value)

    elif expression._metatype == "InvocationExpression":
        body = ", ".join(map(get_label_for_expression, expression.throughParameterMembership))
        expression_label = f"{expression.throughFeatureTyping[0].declaredName}({body})"

    else:
        warn(f"Cannot process {expression._metatype} elements yet!")
    return expression_label


def get_label_for_multiplicity(multiplicity: Element) -> str:
    values = {}
    data = multiplicity._data
    for limit, default in DEFAULT_MULTIPLICITY_LIMITS.items():
        literal_id = (data.get(f"{limit}Bound") or {}).get("@id")
        if literal_id is None:
            values[limit] = default
            continue
        value = multiplicity._model.elements.get(literal_id, {})._data.get("value")
        if value is None:
            value = default
        values[limit] = value
    return f"""{values["lower"]}..{values["upper"]}"""


def get_qualified_label(element: Element, parameter_name_map: dict, start: bool) -> str:
    earlier_name = "Model"

    element_data = element._data
    all_elements = element._model.elements

    if "owner" in element_data:
        if element_data["owner"] is not None:
            element_owner = all_elements[element_data["owner"]["@id"]]
            earlier_name = get_qualified_label(element_owner, parameter_name_map, False)
    else:
        name = element_data["name"]
        return f"{name}"

    printed_name = ""
    if element_data["@id"] in parameter_name_map:
        printed_name = parameter_name_map[element_data["@id"]]
    else:
        printed_name = get_label(element)

    tail = ""
    if start:
        tail = " <<" + element_data["@type"] + ">>"

    earlier_name = f"{earlier_name}::{printed_name}{tail}"

    return earlier_name
