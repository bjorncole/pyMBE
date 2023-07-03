from typing import Any, Dict, List
from uuid import uuid4
import copy

from pymbe.model import Element, Model

def create_element_data_dictionary(name: str, metaclass: str, model: Model, specific_fields: dict):
    """
    Creates a Python dictionary with data for a new KerML/SysML element based on templates from
    base Ecore definitions.
    """

    new_id = str(uuid4())

    new_element_data = copy.deepcopy(model.metamodel.pre_made_dicts[metaclass])

    new_element_data['declaredName'] = name
    for specific_update in specific_fields.keys():
        new_element_data[specific_update] = specific_fields[specific_update]

    new_element_data.update({"@type": metaclass})
    new_element_data.update({"@id": new_id})

    return new_element_data
    

def build_from_classifier_pattern(
    owner: Element,
    name: str,
    model: Model,
    metatype: str,
    specific_fields: Dict[str, Any]
):
    
    """
    Creates a new element using a classifier-style pattern that assumes:
    - The new element will need an owner
    - New element has a name of interest
    - There are no end features to consider
    """

    classifier_dict = create_element_data_dictionary(name=name, metaclass=metatype, model=model, specific_fields=specific_fields)

    new_ele = Element.new(data=classifier_dict, model=model)

    new_element_ownership_pattern(owner=owner, ele=new_ele, model=model, member_kind="OwningMembership")

    return new_ele

def build_from_binary_relationship_pattern(
    source: Element,
    target: Element,
    model: Model,
    metatype: str,
    owned_by_source: bool,
    owns_target: bool,
    alternative_owner: Element,
    specific_fields: Dict[str, Any],
):
    
    """
    Creates a new element using a graph relationship-style pattern that assumes:
    - The new element may be owned by its source or some other element
    - There are source and target elements, each of multiplicity 1
    """

    owned_related_element = []
    owning_related_element = []
    owner = None
    if owns_target:
        owned_related_element = [{"@id": target._id}]
    if owned_by_source:
        owning_related_element = {"@id": source._id}
    if alternative_owner is not None:
        # TODO: Have reasonable exception if this and owned_by_source are both true
        owner = {"@id": alternative_owner._id}
        

    rel_specific = {
        "source": [{"@id": source._id}],
        "ownedRelatedElement": owned_related_element,
        "target": [{"@id": target._id}],
        "owningRelatedElement": owning_related_element,
        "owner": owner
    } | specific_fields

    relationship_dict = create_element_data_dictionary(name="", metaclass=metatype, model=model, specific_fields=rel_specific)

    new_rel = Element.new(data=relationship_dict, model=model)

    model._add_relationship(new_rel)

    return new_rel


# def create_new_classifier(owner: Element, name: str, model: Model, metatype: str, added_fields: Dict[str, Any]):
#     """
#     Creates a new KerML Classifier and sets up relationships to its owner.
#     """

#     # first validate 

#     new_id = str(uuid4())
#     classifier_data = {
#         "elementID": new_id,
#         "owningRelationship": None,
#         "aliasIds": [],
#         "@type": metatype,
#         "ownedRelationship": [],
#         "declaredName": name,
#         "isSufficient": False,
#         "isAbstract": False,
#         "isImpliedIncluded": False,
#         "@id": new_id,
#     } | added_fields

#     new_ele = Element.new(data=classifier_data, model=model)

#     new_element_ownership_pattern(owner=owner, ele=new_ele, model=model)

#     return new_ele


# def create_new_relationship(
#     owner: Element,
#     source: Element,
#     target: Element,
#     model: Model,
#     metatype: str,
#     owned_related_element: Element,
#     owning_related_element: Element,
#     added_fields: Dict[str, Any],
# ):
#     """
#     Create generic KerML/SysML v2 relationship of a given metatype
#     """

#     new_rel_id = str(uuid4())

#     owned_related_element = (
#         [{"@id": owned_related_element._id}] if isinstance(owned_related_element, Element) else []
#     )
#     owning_related_element = (
#         {"@id": owning_related_element._id}
#         if isinstance(owning_related_element, Element)
#         else None
#     )

#     rel_data = {
#         "elementId": new_rel_id,
#         "isImplied": False,
#         "aliasIds": [],
#         "visibility": "public",
#         "@type": metatype,
#         "ownedRelationship": [],
#         "source": [{"@id": source._id}],
#         "ownedRelatedElement": owned_related_element,
#         "isImpliedIncluded": False,
#         "target": [{"@id": target._id}],
#         "owningRelatedElement": owning_related_element,
#         "@id": new_rel_id,
#     } | added_fields

#     new_rel = Element.new(data=rel_data, model=model)

#     model._add_relationship(new_rel)

#     return new_rel


def build_from_feature_pattern(
    owner: Element,
    name: str,
    model: Model,
    specific_fields: Dict[str, Any],
    feature_type: Element,
    direction: str = "",
    metatype: str = "Feature"
):
    
    """
    Creates a new element using a feature-style pattern that assumes:
    - The Feature will have some special kind of membership connecting it to the owner
    - The Feature may have a multiplicity
    - The Feature may have a type
    """

    typing_snippet = None
    direction_snippet = None
    member_kind = ""

    if feature_type is not None:
        typing_snippet = {
            "type": {"@id": feature_type}
        }

    if direction != "":
        direction_snippet = {
            "direction": direction
        }

    specific_fields = typing_snippet | direction_snippet

    feature_dict = create_element_data_dictionary(name=name, metaclass=metatype, model=model, specific_fields=specific_fields)

    new_ele = Element.new(data=feature_dict, model=model)

    # TODO: Add more cases here
    if metatype == "Feature":
        member_kind = "FeatureMembership"

    new_element_ownership_pattern(owner=owner, ele=new_ele, model=model, member_kind=member_kind)

# def create_new_feature(owner: Element,
#                        name: str,
#                        model: Model,
#                        added_fields: Dict[str, Any],
#                        metatype: str = "Feature",
#                        member_kind: str = "FeatureMembership"):
#     """
#     Creates a new KerML Feature and sets up relationships to its owner.
#     """
#     new_id = str(uuid4())

#     feature_data = {
#         "elementID": new_id,
#         "owningRelationship": None,
#         "aliasIds": [],
#         "@type": metatype,
#         "ownedRelationship": [],
#         "declaredName": name,
#         "isUnique": True,
#         "isPortion": False,
#         "isAbstract": False,
#         "isEnd": False,
#         "isImpliedIncluded": False,
#         "isComposite": False,
#         "isReadOnly": False,
#         "isSufficient": False,
#         "isOrdered": False,
#         "direction": "in",
#         "@id": new_id,
#     } | added_fields

#     new_ele = Element.new(data=feature_data, model=model)

#     # TODO: Fix this to FeatureMembership
#     new_element_ownership_pattern(owner=owner, ele=new_ele, model=model, member_kind=member_kind)

#     return new_ele


# def create_new_feature(owner: Element,
#                        name: str,
#                        model: Model,
#                        added_fields: Dict[str, Any],
#                        metatype: str = "Feature",
#                        member_kind: str = "FeatureMembership"):
#     """
#     Creates a new KerML Feature and sets up relationships to its owner.
#     """
#     new_id = str(uuid4())

#     feature_data = {
#         "elementID": new_id,
#         "owningRelationship": None,
#         "aliasIds": [],
#         "@type": metatype,
#         "ownedRelationship": [],
#         "declaredName": name,
#         "isUnique": True,
#         "isPortion": False,
#         "isAbstract": False,
#         "isEnd": False,
#         "isImpliedIncluded": False,
#         "isComposite": False,
#         "isReadOnly": False,
#         "isSufficient": False,
#         "isOrdered": False,
#         "direction": "in",
#         "@id": new_id,
#     } | added_fields

#     new_ele = Element.new(data=feature_data, model=model)

#     # TODO: Fix this to FeatureMembership
#     new_element_ownership_pattern(owner=owner, ele=new_ele, model=model, member_kind=member_kind)

#     return new_ele

def new_element_ownership_pattern(owner: Element, ele: Element, model: Model, member_kind: str = "OwningMembership"):
    """
    Common helper to link new elements to their owners.
    """

    member_name = ""
    if "declaredName" in ele._data:
        member_name = ele.declaredName

    om_added_data = {
        "memberName": member_name,
        "memberElement": {"@id": ele._id},
    }

    new_om = build_from_binary_relationship_pattern(
        source=owner,
        target=ele,
        model=model,
        metatype=member_kind,
        owned_by_source=True,
        owns_target=True,
        alternative_owner=None,
        specific_fields=om_added_data,
    )

    model._add_relationship(new_om)

    # should make this more automatic in core code, but add new_om to owner's ownedRelationship
    # a lot of these entailments will be a pain and need to manage them actively

    owner._data["ownedRelationship"].append({"@id": new_om._id})
    ele._data["owningRelationship"] = {"@id": new_om._id}

    return new_om

# TODO: Move to dedicated reasoning file under interpretation area
def build_superset_classifier(classes : List[Element],
                            super_name: str,
                            owner: Element,
                            model: Model,
                            added_fields: Dict[str, Any],
                            unioned: bool = False
                            ):
    '''
    Take in a list of classifiers and generate a larger set from them. Idea is to have this work with
    individuals and classifiers of multiplicity of 1.
    '''
    new_super = build_from_classifier_pattern(
        owner=owner,
        name=super_name,
        model=model,
        specific_fields=added_fields,
        metatype=classes[0]._metatype)
    
    for clz in classes:
        
        subclass_added_data = {
             'specific': {'@id': clz._id},
             'general': {'@id': new_super._id},
             'subclassifier': {'@id': clz._id},
             'superclassifier': {'@id': new_super._id}
        }

        new_sc = build_from_binary_relationship_pattern(
            source=clz,
            target=new_super,
            model=model,
            metatype='Subclassification',
            owned_by_source=True,
            owns_target=False,
            alternative_owner=None,
            specific_fields=subclass_added_data
        )

        if unioned:
            new_unioning = build_from_binary_relationship_pattern(
                source=new_super,
                target=clz,
                model=model,
                metatype='Unioning',
                owned_by_source=True,
                owns_target=False,
                alternative_owner=None,
                specific_fields={'unioningType': {'@id': clz._id}}
            )
        
    return new_super