from typing import Any, Dict
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

    return new_element_data
    

def create_new_classifier(owner: Element, name: str, model: Model):
    """
    Creates a new KerML Classifier and sets up relationships to its owner.
    """

    # first validate 

    new_id = str(uuid4())
    classifier_data = {
        "elementID": new_id,
        "owningRelationship": None,
        "aliasIds": [],
        "@type": "Classifier",
        "ownedRelationship": [],
        "declaredName": name,
        "isSufficient": False,
        "isAbstract": False,
        "isImpliedIncluded": False,
        "@id": new_id,
    }

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

def own_new_element(owner: Element, ele: Element, model: Model):
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
        metatype="OwningMembership",
        owned_related_element=ele,
        owning_related_element=owner,
        added_fields=om_added_data,
    )

    model._add_relationship(new_om)

    # should make this more automatic in core code, but add new_om to owner's ownedRelationship
    # a lot of these entailments will be a pain and need to manage them actively

    owner._data["ownedRelationship"].append({"@id": new_om._id})
