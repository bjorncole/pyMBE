# Module for computing useful labels and signatures for visualization

def m1_signature(element: dict, element_world: dict) -> str:
    if 'name' in element and element['name'] is not None:
        if 'type' in element and element['type'] is not None and \
                len(element['type']) > 0 and element_world[element['type'][0]['@id']] is not None:
            return element['name'] + ': ' + str(element_world[element['type'][0]['@id']]['name'])
        return element['name']
    elif '@type' in element and element['@type'] == 'FeatureReferenceExpression':
        refer = element_world[element['referent']['@id']]
        return 'FRE.' + refer['name']
    elif '@type' in element and element['@type'] == 'Expression':
        input_list = []
        input_id_list = []
        for indx, oper in enumerate(element['input']):
            input_list.append(element_world[oper['@id']]['name'])
            input_id_list.append(oper['@id'])
        if len(input_list) > 0:
            ins = ', '.join(input_list)
        else:
            ins = ''
        body = ''
        # Scan memberships to find non-parameter members
        for owned_member in element['ownedMember']:
            owned_member_id = owned_member['@id']
            if owned_member_id != element['result']['@id'] and owned_member_id not in input_id_list:
                body_element = element_world[owned_member_id]
                body = m1_signature(body_element, element_world)

        return body + ' (' + ins + ') => ' + element_world[element['result']['@id']]['name']
    elif '@type' in element and element['@type'] == 'OperatorExpression':
        input_list = []
        for indx, oper in enumerate(element['input']):
            input_list.append(element_world[oper['@id']]['name'])
        if len(input_list) > 0:
            ins = ', '.join(input_list)
        else:
            ins = ''
        return element['operator'] + ' (' + ins + ') => ' + element_world[element['result']['@id']]['name']
    elif '@type' in element and element['@type'] == 'InvocationExpression':
        invoked = ''
        if 'type' in element and element['type'] is not None and \
                len(element['type']) > 0 and element_world[element['type'][0]['@id']] is not None:
            invoked = str(element_world[element['type'][0]['@id']]['name'])
        input_list = []
        for indx, oper in enumerate(element['input']):
            input_list.append(element_world[oper['@id']]['name'])
        if len(input_list) > 0:
            ins = ', '.join(input_list)
        else:
            ins = ''
        return invoked + ' (' + ins + ') => ' + element_world[element['result']['@id']]['name']
    elif '@id' in element:
        return element['@id'] + ' <' + element['@type'] + '>'
    else:
        return 'blank'