# a collection of convenience methods to navigate the metamodel when inspecting user models

from ..graph.lpg import SysML2LabeledPropertyGraph


def feature_lower_multiplicity(feature: dict, lpg: SysML2LabeledPropertyGraph):
    if feature['multiplicity'] is not None:
        if '@id' in feature['multiplicity']:
            mult = lpg.elements_by_id[feature['multiplicity']['@id']]
            if '@id' in mult['lowerBound']:
                return lpg.elements_by_id[mult['lowerBound']['@id']]['value']
    return 1


def feature_upper_multiplicity(feature: dict, lpg: SysML2LabeledPropertyGraph):
    if feature['multiplicity'] is not None:
        if '@id' in feature['multiplicity']:
            mult = lpg.elements_by_id[feature['multiplicity']['@id']]
            if '@id' in mult['upperBound']:
                return lpg.elements_by_id[mult['upperBound']['@id']]['value']
                
    return 1