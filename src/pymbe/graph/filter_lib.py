
def banded_graph_filter():
    """
    Generate library settings for a "banded graph" of types, generalization, and feature membership to capture
    both SysML v1 and v2 styled composition structures
    :return: Dictionary with configuration to apply to the LPG filter function
    """

    filter_dict = {
        'nodes': None,
        'node_types': None,
        'edges': None,
        'edge_types': ("Superclassing", "FeatureMembership", "FeatureTyping"),
        'reverse_edge_types': ("FeatureMembership", "FeatureTyping")
    }

    return filter_dict

def expanded_banded_graph_filter():
    """
    "Banded graph" that includes not just parts and typing but also memberships for parameters
    :return: Dictionary with configuration to apply to the LPG filter function
    """

    filter_dict = {
        'nodes': None,
        'node_types': None,
        'edges': None,
        'edge_types': ("Superclassing", "FeatureMembership", "ParameterMembership", "ReturnParameterMembership",
                       "FeatureTyping", "FeatureValue"),
        'reverse_edge_types': ("FeatureMembership", "FeatureTyping",
                               "ParameterMembership", "ReturnParameterMembership", "FeatureValue")
    }

    return filter_dict