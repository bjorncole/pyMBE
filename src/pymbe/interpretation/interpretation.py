class Instance:
    """
    A class to represent instances of real things in the M0 universe interpreted from the model.
    Sequences of instances are intended to follow the mathematical base semantics of SysML v2.
    """
    def __init__(self, name, index, pre_bake):
        self.name = shorten_name(name, shorten_pre_bake=pre_bake) + '#' + str(index)

    def __repr__(self):
        return self.name


class ValueHolder:
    """
    A class to represent instances of the attribution of real things in the M0 universe interpreted from the model.
    Sequences of instances and value holders are intended to follow the mathematical base semantics of SysML v2.
    Additionally, the value holders are meant to be variables in numerical analyses.
    """
    def __init__(self, path, name, value, base_att, index):
        # path is list of instance references
        self.holder_string = ''
        for indx, step in enumerate(path):
            if indx == 0:
                self.holder_string = str(step)
            else:
                self.holder_string = self.holder_string + '.' + str(step)
        self.holder_string = self.holder_string + '.' + name + '#' + str(index)
        self.value = value
        self.base_att = base_att

    def __repr__(self):
        if self.value is not None:
            return self.holder_string + ' (' + str(self.value) + ')'
        else:
            return self.holder_string + ' (unset)'


class LiveExpressionNode:
    """
    A class to be instances of expressions that can support computations in the M0 space. Also, this is where
    implementation code for a specific expression type can be placed are segments of a tree can be subsumed by a
    specific procedure.
    """
    def __init__(self, path, expr, base_att):
        # path is list of instance references
        self.holder_string = expr
        self.path = path
        self.base_att = base_att

    def __repr__(self):
        return self.holder_string


def shorten_name(name, shorten_pre_bake=None):
    """
    Helper to get short names for reporting many instances
    :param name: Existing name to shorten
    :param shorten_pre_bake: A pre-computed dictionary mapping long names to custom short names
    :return: a shortened version of the input name if the input is longer than five characters
    """
    short_name = ""
    if not name:
        return "Unnamed"
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
