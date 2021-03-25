import model_loading


class Instance:
    """
    A class to represent instances of real things in the M0 universe interpreted from the model.
    Sequences of instances are intended to follow the mathematical base semantics of SysML v2.
    """
    def __init__(self, name, index):
        self.name = shorten_name(name) + '#' + str(index)

    def __repr__(self):
        return self.name


class ValueHolder:
    """
    A class to represent instances of the attribution of real things in the M0 universe interpreted from the model.
    Sequences of instances and value holders are intended to follow the mathematical base semantics of SysML v2.
    Additionally, the value holders are meant to be variables in numerical analyses.
    """
    def __init__(self, path, name, value, base_att):
        # path is list of instance references
        self.holder_string = ''
        for indx, step in enumerate(path):
            if indx == 0:
                self.holder_string = str(step)
            else:
                self.holder_string = self.holder_string + '.' + str(step)
        self.holder_string = self.holder_string + '.' + name
        self.value = value
        self.base_att = base_att

    def __repr__(self):
        if self.value is not None:
            return self.holder_string + ' (' + str(self.value) + ')'
        else:
            return self.holder_string + ' (unset)'


def shorten_name(name, shorten_pre_bake=None):
    """
    Helper to get short names for reporting many instances
    :param name: Existing name to shorten
    :param shorten_pre_bake: A pre-computed dictionary mapping long names to custom short names
    :return: a shortened version of the input name if the input is longer than five characters
    """
    short_name = ''
    if len(name) > 5:
        if shorten_pre_bake is not None:
            if name in shorten_pre_bake:
                return shorten_pre_bake[name]
        space_place = name.find(' ')
        if space_place > -1:
            short_name = short_name + name[0]
            short_name = short_name + name[space_place + 1]
            next_space = name.find(' ', space_place + 1)
            while next_space > -1:
                short_name = short_name + name[next_space + 1]
                next_space = name.find(' ', next_space + 1)
            return short_name
    return name


def get_att_literal_values(att_use):
    literal_values = []
    for att_member in att_use['ownedMember']:
        if att_member['@id'] in model_loading.lookup.id_memo_dict:
            if model_loading.lookup.id_memo_dict[att_member['@id']]['@type'] == 'LiteralReal':
                literal_values.append(model_loading.lookup.id_memo_dict[att_member['@id']])

    return literal_values