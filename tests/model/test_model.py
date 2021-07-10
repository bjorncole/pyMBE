from tests.conftest import all_models

from pymbe.model import Element, Model


def test_respect_of_sysml(all_models):
    for model in all_models.values():
        for element in model.elements.values():
            element_attrs = set(super(Element).__dir__())
            sysml_attrs = set(element._data)
            common_attrs = element_attrs.intersection(sysml_attrs)
            assert not common_attrs, f"Found common attributes with SysML: {common_attrs}"
