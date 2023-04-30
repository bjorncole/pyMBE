import pytest

from pymbe.model import Element, Model

def test_pythonic_attributes(basic_load_files):
    '''
    Test that primary attributes are loaded into elements such that they can be referenced as normal Python prpperties
    '''

    level3 = basic_load_files["Level3"]

    literals = basic_load_files["Literals"]

    key_invar = [invariant for invariant in list(level3.elements.values()) if invariant._metatype == 'Invariant'][0]

    assert hasattr(key_invar.ownedRelationship[0].ownedRelatedElement[0], "operator")
    assert key_invar.ownedRelationship[0].ownedRelatedElement[0].operator == "=="

    literal_test_literals = [literal for literal in list(literals.elements.values()) if literal._metatype == 'LiteralRational']

    assert hasattr(literal_test_literals[0], "value")
    assert literal_test_literals[0].value == 3.0

    assert True

def test_pythonic_references(basic_load_files):
    '''
    Test that primary references are loaded into elements such that they can be referenced as normal Python prpperties
    '''

    assert True

def test_pythonic_through_reverse(basic_load_files):
    '''
    Test that 'through' and 'reverse' Pythonic properties work correctly
    '''

    assert True