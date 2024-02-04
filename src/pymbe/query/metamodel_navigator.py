# a collection of convenience methods to navigate the metamodel when inspecting user models


def is_type_undefined_mult(type_ele):
    if "throughOwningMembership" not in type_ele._derived:
        return True
    mult_range = [
        mr for mr in type_ele.throughOwningMembership if mr["@type"] == "MultiplicityRange"
    ]
    if len(mult_range) == 0:
        return True
    return False


def is_multiplicity_one(type_ele):
    if "throughOwningMembership" not in type_ele._derived:
        return False
    multiplicity_range = [
        mr for mr in type_ele.throughOwningMembership if mr["@type"] == "MultiplicityRange"
    ][0]
    literal_value = [
        li.value
        for li in multiplicity_range.throughOwningMembership
        if li["@type"] == "LiteralInteger"
    ]

    if len(literal_value) == 1:
        if literal_value[0] == 1:
            return True
    if len(literal_value) == 2:
        if literal_value[0] == 1 and literal_value[1] == 1:
            return True
    return False


def is_multiplicity_specific_finite(type_ele):
    if "throughOwningMembership" not in type_ele._derived:
        return False
    multiplicity_range = [
        mr for mr in type_ele.throughOwningMembership if mr["@type"] == "MultiplicityRange"
    ][0]
    literal_value = [
        li.value
        for li in multiplicity_range.throughOwningMembership
        if li["@type"] == "LiteralInteger"
    ]

    if len(literal_value) == 1:
        if literal_value[0] > 1:
            return True
    if len(literal_value) == 2:
        if literal_value[0] > 1 and literal_value[0] == literal_value[1]:
            return True
    return False


def get_finite_multiplicity_types(model):
    model_types = [
        ele for ele in model.elements.values() if ele._metatype in ("Feature", "Classifier")
    ]

    return [
        finite_type
        for finite_type in model_types
        if is_multiplicity_one(finite_type) or is_multiplicity_specific_finite(finite_type)
    ]


def get_lower_multiplicty(type_ele):
    lower_mult = -1
    if "throughOwningMembership" not in type_ele._derived:
        return lower_mult
    multiplicity_ranges = [
        mr for mr in type_ele.throughOwningMembership if mr["@type"] == "MultiplicityRange"
    ]
    if len(multiplicity_ranges) == 1:
        literal_value = [
            li.value
            for li in multiplicity_ranges[0].throughOwningMembership
            if li["@type"] == "LiteralInteger"
        ]
    elif len(multiplicity_ranges) > 1:
        literal_value = [
            li.value
            for li in multiplicity_ranges[0].throughOwningMembership
            if li["@type"] == "LiteralInteger"
        ]

    if len(literal_value) > 0:
        lower_mult = int(literal_value[0])

    return lower_mult


def get_upper_multiplicty(type_ele):
    upper_mult = -1
    if "throughOwningMembership" not in type_ele._derived:
        return upper_mult
    multiplicity_ranges = [
        mr for mr in type_ele.throughOwningMembership if mr["@type"] == "MultiplicityRange"
    ]
    if len(multiplicity_ranges) == 1:
        literal_value = [
            li.value
            for li in multiplicity_ranges[0].throughOwningMembership
            if li["@type"] == "LiteralInteger"
        ]
    elif len(multiplicity_ranges) > 1:
        literal_value = [
            li.value
            for li in multiplicity_ranges[1].throughOwningMembership
            if li["@type"] == "LiteralInteger"
        ]

    upper_mult = int(literal_value[0])

    return upper_mult


def identify_connectors_one_side(connectors):
    one_sided = []
    for connector in connectors:
        if "throughEndFeatureMembership" in connector._derived:
            for end_feature in connector.throughEndFeatureMembership:

                if "throughReferenceSubsetting" in end_feature._derived:
                    if (
                        is_multiplicity_one(end_feature.throughReferenceSubsetting[0])
                        and connector not in one_sided
                    ):
                        one_sided.append(connector)

    return one_sided

def does_behavior_have_write_features(behavior):

    if hasattr(behavior, "throughFeatureMembership"):

        candidate_features = behavior.throughFeatureMembership

        for cf in candidate_features:

            if cf._metatype == 'Step':
                step = cf

                if hasattr(step, "throughFeatureTyping"):
                    candidate_types = step.throughFeatureTyping
                    for ct in candidate_types:
                        if ct.declaredName == 'FeatureWritePerformance':
                            return True

    return False

def has_type_named(feature, type_name):
    if hasattr(feature, "throughFeatureTyping"):
        for ft in feature.throughFeatureTyping:
            if ft.declaredName == type_name:
                return True
    return False

def get_most_specific_feature_type(feature):

    if hasattr(feature, "throughFeatureTyping"):
        if len(feature.throughFeatureTyping) == 1:
            return feature.throughFeatureTyping[0]

    if hasattr(feature, "throughRedefinition"):
        if len(feature.throughRedefinition) == 1:
            redef_feature = feature.throughRedefinition[0]

            if hasattr(redef_feature, "throughFeatureTyping"):
                if len(redef_feature.throughFeatureTyping) == 1:
                    return redef_feature.throughFeatureTyping[0]
                
def get_all_more_general_types(typ):
    """
    Recursively navigate along Specialization relationships to find all the more general
    types of the given type
    """

    local_more_general =  typ.throughFeatureTyping + \
                            typ.reverseSubclassification + \
                            typ.throughRedefinition
    
    total_general = local_more_general + \
        [item for local_general in local_more_general for item in get_all_more_general_types(local_general)]
    
    return total_general