from pymbe.model import Model, Element

from uuid import uuid4

def create_new_classifier(owner : Element, name : str, model: Model):
    new_id = str(uuid4())
    classifier_data = {
        'elementID' : new_id,
        'owningRelationship': None,
        'aliasIds': [],
        '@type': 'Classifier',
        'ownedRelationship': [],
        'declaredName': name,
        'isSufficient': False,
        'isAbstract': False,
        'isImpliedIncluded': False,
        '@id': new_id
    }
    
    Element.new(data=classifier_data, model=model)
    
    om_new_id = str(uuid4())
    om_data = {
        'elementId': om_new_id,
         'isImplied': False,
         'aliasIds': [],
         'visibility': 'public',
         '@type': 'OwningMembership',
         'ownedRelationship': [],
         'memberName': name,
         'source': [{'@id': owner._id}],
         'ownedRelatedElement': [{'@id': new_id}],
         'isImpliedIncluded': False,
         'target': [{'@id': new_id}],
         'owningRelatedElement': {'@id': owner._id},
         'memberElement': {'@id': new_id},
         '@id': om_new_id
    }
    
    Element.new(data=om_data, model=model)
    
    # should make this more automatic in core code, but add new_om to owner's ownedRelationship
    # a lot of these entailments will be a pain and need to manage them actively
    
    owner._data["ownedRelationship"].append({'@id': om_new_id})
    
    return True