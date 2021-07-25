from dataclasses import dataclass
from ..model import Element, Model
from ..label import get_label

class InterpretationSequence(tuple):
    """
    A data class to represent a single sequence within a model interpretation. Objects of this class should support
    the drawing of interpretation diagrams and be the eventual target of validity checkers.
    """

    def __init__(self, elements: list):
        self.sequence = tuple(elements)
        self.owning_entry = None
    def get_line_ends(self):
        # placeholder for using M1 reference to figure out what the right ends for the connector line are
        pass
    def get_nesting_list(self):
        # placeholder for using M1 reference to figure out what the path of parent shapes are
        pass

DEF_BOX_KINDS = ("PartDefinition", "PortDefinition")
USE_BOX_KINDS = ("PartUsage")
LINE_KINDS = ("ConnectionUsage")
PORT_BOX_KINDS = ("PortUsage")


class InterpretationDictionaryEntry:
    """
    A data class to represent a key value pair for a master interpretation dictionary, which points from
    M1 user model elements to a set of sequences of atoms that are the interpretation
    """

    def __init__(self, m1_base: Element, interprets: set):
        self.key = m1_base._id
        self.value = set()
        self.base = m1_base
        for item in interprets:
            self.value.add(item)
            # link the sequence owning entry back here to leave a breadcrumb for plotting, checking, etc.
            item.owning_entry = self
        # build hinting for diagram
        if m1_base.get("@type") in DEF_BOX_KINDS:
            self.draw_kind = "Box"
        elif m1_base.get("@type") in USE_BOX_KINDS:
            self.draw_kind = "Nested Box"
        elif m1_base.get("@type") in LINE_KINDS:
            self.draw_kind = "Line"
        elif m1_base.get("@type") in PORT_BOX_KINDS:
            self.draw_kind = "Port"

    def __repr__(self):
        return f'Entry: <{get_label(self.base)}, {self.value}>'

class Instance:
    """
    A class to represent instances of real things in the M0 universe interpreted from the model.
    Sequences of instances are intended to follow the mathematical base semantics of SysML v2.
    """
    def __init__(self, name, index, pre_bake):
        self.name = f"{shorten_name(name, shorten_pre_bake=pre_bake)}#{index}"

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
        self.holder_string = ""
        for indx, step in enumerate(path):
            if indx == 0:
                self.holder_string = str(step)
            else:
                self.holder_string = f"{self.holder_string}.{step}"
        self.holder_string = f"{self.holder_string}.{name}#{index}"
        self.value = value
        self.base_att = base_att

    def __repr__(self):
        value = self.value if self.value is not None else "unset"
        return f"{self.holder_string} ({value})"


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


def shorten_name(name: str, shorten_pre_bake: dict = None) -> str:
    """
    Helper to get short names for reporting many instances

    :param name: Existing name to shorten
    :param shorten_pre_bake: A pre-computed dictionary mapping long names to custom short names
    :return: a shortened version of the input name if the input is longer than five characters
    """
    short_name = ""
    shorten_pre_bake = shorten_pre_bake or {}
    if not name:
        return "Unnamed"
    if len(name) > 5:
        if name in shorten_pre_bake:
            return shorten_pre_bake[name]
        space_place = name.find(" ")
        if space_place > -1:
            short_name = short_name + name[0]
            short_name = short_name + name[space_place + 1]
            next_space = name.find(" ", space_place + 1)
            while next_space > -1:
                short_name = short_name + name[next_space + 1]
                next_space = name.find(" ", next_space + 1)
            return short_name
    return name

def repack_instance_dictionaries(instance_dict: dict, mdl: Model):
    """
    Temporary method to repack the instance dictionaries into objects to be sure this is how we want things to work
    :param instance_dict: Completed instance dictionary
    :return: An object version of the instance dictionary
    """

    instance_list = []

    for key, sequence_set in instance_dict.items():
        new_set = set()
        for seq in sequence_set:
            new_seq = InterpretationSequence(seq)
            new_set.add(new_seq)
        entry = InterpretationDictionaryEntry(mdl.elements[key], new_set)
        instance_list.append(entry)

    return instance_list