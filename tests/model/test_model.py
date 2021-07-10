from copy import deepcopy

from tests.conftest import all_models, kerbal_model

from pymbe.model import Element, Model


def test_respect_of_sysml(all_models):
    for model in all_models.values():
        for element in model.elements.values():
            element_attrs = set(super(Element).__dir__())
            sysml_attrs = set(element._data)
            common_attrs = element_attrs.intersection(sysml_attrs)
            assert not common_attrs, f"Found common attributes with SysML: {common_attrs}"


def test_kerbal_model(kerbal_model):
    model = kerbal_model
    kerbal = model.ownedElement["Kerbal"]

    assert kerbal.name == "Kerbal", f"Element name should be 'Kerbal', not '{kerbal.name}'"
    assert kerbal == kerbal._id, f"Element should equate to its id"
    assert kerbal == deepcopy(kerbal._data), f"Element should equate to its _data"

    my_rocket = kerbal(name="My Rocket")
    assert my_rocket.name == "My Rocket", f"Instance should be called 'My Rocket', not '{my_rocket.name}'"

    assert kerbal.ownedElement["Parts Library"].ownedElement["FL-T200 Fuel Tank"].ownedElement["Empty Mass"].ownedElement[0].value == 0.125

    for element in model.elements.values():
        if element._metatype == "ReturnParameterMembership":
            a_return_parameter_membership = element
    assert isinstance(a_return_parameter_membership.relatedElement[0].value, int)

    assert a_return_parameter_membership.target[0].reverseReturnParameterMembership[0] == a_return_parameter_membership.relatedElement[0]