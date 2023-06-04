from typing import Any, Dict, List
from uuid import uuid4

from pymbe.model import Element, Model


def create_new_classifier(owner: Element, name: str, model: Model, metatype: str, added_fields: Dict[str, Any]):
    """
    Creates a new KerML Classifier and sets up relationships to its owner.
    """
    new_id = str(uuid4())
    classifier_data = {
        "elementID": new_id,
        "owningRelationship": None,
        "aliasIds": [],
        "@type": metatype,
        "ownedRelationship": [],
        "declaredName": name,
        "isSufficient": False,
        "isAbstract": False,
        "isImpliedIncluded": False,
        "@id": new_id,
    } | added_fields

    new_ele = Element.new(data=classifier_data, model=model)

    own_new_element(owner=owner, ele=new_ele, model=model)

    return new_ele


def create_new_relationship(
    owner: Element,
    source: Element,
    target: Element,
    model: Model,
    metatype: str,
    owned_related_element: Element,
    owning_related_element: Element,
    added_fields: Dict[str, Any],
):
    """
    Create generic KerML/SysML v2 relationship of a given metatype
    """

    new_rel_id = str(uuid4())

    owned_related_element = (
        [{"@id": owned_related_element._id}] if isinstance(owned_related_element, Element) else []
    )
    owning_related_element = (
        {"@id": owning_related_element._id}
        if isinstance(owning_related_element, Element)
        else None
    )

    rel_data = {
        "elementId": new_rel_id,
        "isImplied": False,
        "aliasIds": [],
        "visibility": "public",
        "@type": metatype,
        "ownedRelationship": [],
        "source": [{"@id": source._id}],
        "ownedRelatedElement": owned_related_element,
        "isImpliedIncluded": False,
        "target": [{"@id": target._id}],
        "owningRelatedElement": owning_related_element,
        "@id": new_rel_id,
    } | added_fields

    new_rel = Element.new(data=rel_data, model=model)

    model._add_relationship(new_rel)

    return new_rel

def create_new_feature(owner: Element,
                       name: str,
                       model: Model,
                       added_fields: Dict[str, Any],
                       metatype: str = "Feature",
                       member_kind: str = "FeatureMembership"):
    """
    Creates a new KerML Feature and sets up relationships to its owner.
    """
    new_id = str(uuid4())

    feature_data = {
        "elementID": new_id,
        "owningRelationship": None,
        "aliasIds": [],
        "@type": metatype,
        "ownedRelationship": [],
        "declaredName": name,
        "isUnique": True,
        "isPortion": False,
        "isAbstract": False,
        "isEnd": False,
        "isImpliedIncluded": False,
        "isComposite": False,
        "isReadOnly": False,
        "isSufficient": False,
        "isOrdered": False,
        "direction": "in",
        "@id": new_id,
    } | added_fields

    new_ele = Element.new(data=feature_data, model=model)

    # TODO: Fix this to FeatureMembership
    own_new_element(owner=owner, ele=new_ele, model=model, member_kind=member_kind)

    return new_ele


def own_new_element(owner: Element, ele: Element, model: Model, member_kind: str = "OwningMembership"):
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

    new_om = create_new_relationship(
        owner=owner,
        source=owner,
        target=ele,
        model=model,
        metatype=member_kind,
        owned_related_element=ele,
        owning_related_element=owner,
        added_fields=om_added_data,
    )

    model._add_relationship(new_om)

    # should make this more automatic in core code, but add new_om to owner's ownedRelationship
    # a lot of these entailments will be a pain and need to manage them actively

    owner._data["ownedRelationship"].append({"@id": new_om._id})

# TODO: Move to dedicated reasoning file under interpretation area
def create_super_classifier(classes : List[Element],
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
    new_super = create_new_classifier(owner=owner, name=super_name, model=model, added_fields=added_fields, metatype=classes[0]._metatype)
    
    for clz in classes:
        
        subclass_added_data = {
             'specific': {'@id': clz._id},
             'general': {'@id': new_super._id},
             'subclassifier': {'@id': clz._id},
             'superclassifier': {'@id': new_super._id}
        }
        
        new_sc = create_new_relationship(
            source=clz,
            target=new_super,
            owner=clz,
            model=model,
            metatype='Subclassification',
            owned_related_element=None,
            owning_related_element=clz,
            added_fields=subclass_added_data
        )

        if unioned:
            new_unioning = create_new_relationship(
                source=new_super,
                target=clz,
                owner=new_super,
                model=model,
                metatype='Unioning',
                owned_related_element=None,
                owning_related_element=new_super,
                added_fields={'unioningType': {'@id': clz._id}}
            )
        
    return new_super