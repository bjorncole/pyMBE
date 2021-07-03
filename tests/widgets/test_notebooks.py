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
