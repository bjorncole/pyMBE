# a collection of convenience methods to navigate the metamodel when inspecting user models

from ..client import SysML2Client


def feature_lower_multiplicity(feature: dict, client: SysML2Client):
    if feature['multiplicity'] is not None:
        if '@id' in feature['multiplicity']:
            mult = client.elements_by_id[feature['multiplicity']['@id']]
            if '@id' in mult['lowerBound']:
                return client.elements_by_id[mult['lowerBound']['@id']]['value']

    return 1


def feature_upper_multiplicity(feature: dict, client: SysML2Client):
    if feature['multiplicity'] is not None:
        if '@id' in feature['multiplicity']:
            mult = client.elements_by_id[feature['multiplicity']['@id']]
            if '@id' in mult['upperBound']:
                return client.elements_by_id[mult['upperBound']['@id']]['value']

    return 1