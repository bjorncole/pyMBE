from testbook import testbook


@testbook("notebooks/Tutorial.ipynb", execute=True)
def test_tutorial(tb):
    lpg = tb.ref("lpg")
    client = tb.ref("client")

    assert len(lpg.elements_by_id) > 0

    assert len(lpg.elements_by_id) == len(client.elements_by_id)

    assert not set(lpg.elements_by_id).symmetric_difference(set(client.elements_by_id))


@testbook("dev_doc/Playbook Explorer Parts Test.ipynb", execute=True)
def test_simple_parts_explorer(tb):
    m0_interpretation = tb.ref("m0_interpretation")
    assert m0_interpretation


@testbook("dev_doc/SysML Model.ipynb", execute=True)
def test_sysml_model(tb):
    an_element = tb.ref("an_element")
    assert an_element._id == "78c8e7e1-1ac0-4a45-ac30-830ec479abb2"
